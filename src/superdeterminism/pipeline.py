from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from superdeterminism.models import (
    Action,
    DetClass,
    NodeKind,
    Recommendation,
    Span,
    Trace,
)

N_MIN_DEFAULT = 30
SCHEMA_OK_MIN = 0.80
P_MODE_MIN = 0.70
HARD_OVERRIDE = re.compile(
    r"(refund|commit|payment|payout|auth|oauth|pii|password|secret|spend|charge)",
    re.I,
)
DISCLAIMER = "simulation != production; canary is confirmatory"
# ponytail: text only; not a deploy button; confirmatory after a human apply
CANARY_CHECKLIST = (
    "Keep the node name; change only the callable.",
    "Do not auto-apply a scaffold or rewrite graph.py in place.",
    "Re-record traces after apply — old tapes are not comparable.",
    "Compare the same outcome vector (schema, failure rate, task success) on a held-out slice.",
    "ABSTAIN if the canary interval includes zero or n is below n_min.",
    "Sensitive nodes (refund/commit/payment/auth/PII) stay deterministic gates.",
    "simulation != production; this list is confirmatory, not an A/B platform.",
)

_OP_TO_KIND = {
    "chat": NodeKind.LLM_REASONER,
    "generate_content": NodeKind.LLM_REASONER,
    "text_completion": NodeKind.LLM_REASONER,
    "plan": NodeKind.LLM_REASONER,
    "execute_tool": NodeKind.DETERMINISTIC_TOOL,
    "invoke_agent": NodeKind.SUBAGENT,
    "create_agent": NodeKind.SUBAGENT,
    "invoke_workflow": NodeKind.WORKFLOW,
    "retrieval": NodeKind.RETRIEVER,
    "search_memory": NodeKind.RETRIEVER,
}


def _attr_get(attrs: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in attrs and attrs[key] not in (None, ""):
            return attrs[key]
    return None


def _unwrap_otlp_value(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    for k in ("stringValue", "intValue", "doubleValue", "boolValue"):
        if k in value:
            raw = value[k]
            return int(raw) if k == "intValue" and isinstance(raw, str) else raw
    if "arrayValue" in value:
        return [_unwrap_otlp_value(v) for v in value["arrayValue"].get("values", [])]
    return value


def _otlp_attrs(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return {str(k): v for k, v in raw.items()}
    out: dict[str, Any] = {}
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict) or "key" not in item:
            continue
        out[str(item["key"])] = _unwrap_otlp_value(item.get("value"))
    return out


def _span_from_mapping(item: dict[str, Any]) -> Span:
    attrs = item.get("attributes", {})
    if isinstance(attrs, list):
        attrs = _otlp_attrs(attrs)
    elif not isinstance(attrs, dict):
        attrs = {}
    tokens = item.get("tokens")
    if tokens is None:
        tokens = _attr_get(attrs, "gen_ai.usage.input_tokens", "gen_ai.usage.prompt_tokens") or 0
    return Span(
        name=str(item.get("name") or item.get("span_name") or "unnamed"),
        attributes=dict(attrs),
        input=item.get("input"),
        output=item.get("output"),
        tokens=int(tokens or 0),
        latency_ms=float(item.get("latency_ms") or 0.0),
        error=bool(item.get("error") or item.get("status") == "ERROR"),
    )


def _iter_otlp_spans(payload: Any) -> Iterable[dict[str, Any]]:
    if not isinstance(payload, dict):
        return
    for resource in payload.get("resourceSpans") or payload.get("resource_spans") or []:
        for scope in resource.get("scopeSpans") or resource.get("scope_spans") or []:
            for span in scope.get("spans") or []:
                yield span


def load_traces(payload: Any) -> list[Trace]:
    """Accept OTLP JSON, {traces: [...]}, a list of traces, or a list of spans."""
    if isinstance(payload, dict) and (
        "resourceSpans" in payload or "resource_spans" in payload
    ):
        return [Trace(spans=[_span_from_mapping(s) for s in _iter_otlp_spans(payload)])]
    if isinstance(payload, dict) and "traces" in payload:
        traces = []
        for t in payload["traces"]:
            spans = t.get("spans", t) if isinstance(t, dict) else t
            traces.append(Trace(spans=[_span_from_mapping(s) for s in spans]))
        return traces
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        if "spans" in payload[0]:
            return [
                Trace(spans=[_span_from_mapping(s) for s in t.get("spans", [])])
                for t in payload
            ]
        return [Trace(spans=[_span_from_mapping(s) for s in payload])]
    raise ValueError("unrecognized trace payload")


def load_traces_path(path: Path) -> list[Trace]:
    return load_traces(json.loads(path.read_text(encoding="utf-8")))


def classify_span(span: Span) -> tuple[str, NodeKind, DetClass]:
    attrs = span.attributes
    op = str(
        _attr_get(attrs, "gen_ai.operation.name", "gen_ai.operation") or ""
    ).lower()
    tool = _attr_get(attrs, "gen_ai.tool.name")
    node_id = str(
        _attr_get(attrs, "langgraph_node", "gen_ai.agent.name", "gen_ai.tool.name")
        or span.name
    )
    kind = _OP_TO_KIND.get(op, NodeKind.UNKNOWN)
    if kind == NodeKind.UNKNOWN:
        name = span.name.lower()
        if name.startswith("execute_tool") or "tool" in name:
            kind = NodeKind.DETERMINISTIC_TOOL
        elif name.startswith("chat") or "llm" in name:
            kind = NodeKind.LLM_REASONER
        elif "retriev" in name:
            kind = NodeKind.RETRIEVER
        elif "agent" in name:
            kind = NodeKind.SUBAGENT
        elif "workflow" in name:
            kind = NodeKind.WORKFLOW
    if kind == NodeKind.DETERMINISTIC_TOOL and (
        _attr_get(attrs, "gen_ai.tool.type") == "datastore" or "search" in (tool or "")
    ):
        kind = NodeKind.RETRIEVER
    det = {
        NodeKind.DETERMINISTIC_TOOL: DetClass.DETERMINISTIC,
        NodeKind.RETRIEVER: DetClass.STOCHASTIC_INDEX,
        NodeKind.LLM_REASONER: DetClass.LLM,
        NodeKind.SUBAGENT: DetClass.COMPOSITE,
        NodeKind.ROUTER: DetClass.DETERMINISTIC,
        NodeKind.WORKFLOW: DetClass.COMPOSITE,
        NodeKind.UNKNOWN: DetClass.COMPOSITE,
    }[kind]
    temp = _attr_get(attrs, "gen_ai.request.temperature")
    seed = _attr_get(attrs, "gen_ai.request.seed")
    if kind == NodeKind.LLM_REASONER and seed is not None and str(temp) in {"0", "0.0"}:
        det = DetClass.LLM_SEEDED
    return node_id, kind, det


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, default=str)
    except TypeError:
        return str(value)


def _is_schema(value: Any) -> bool:
    if isinstance(value, (dict, list)):
        return True
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text or text[0] not in "{[":
        return False
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return False
    return isinstance(parsed, (dict, list))


def wilson_lower(successes: int, n: int, z: float = 1.96) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    centre = phat + z * z / (2 * n)
    spread = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))
    return max(0.0, (centre - spread) / denom)


def recommend_traces(
    traces: list[Trace],
    *,
    n_min: int = N_MIN_DEFAULT,
) -> list[Recommendation]:
    """L0 / observational recommend. Estimator is proxy, not L2 do_policy."""
    buckets: dict[str, dict[str, Any]] = {}
    for trace in traces:
        for span in trace.spans:
            node_id, kind, det = classify_span(span)
            bucket = buckets.setdefault(
                node_id,
                {
                    "kind": kind,
                    "det": det,
                    "outputs": [],
                    "errors": 0,
                    "n": 0,
                },
            )
            bucket["n"] += 1
            bucket["outputs"].append(span.output)
            bucket["errors"] += int(span.error)
            # ponytail: last-write kind/det; mixed ops on one name need P1 split
            bucket["kind"] = kind
            bucket["det"] = det

    recs: list[Recommendation] = []
    for node_id, bucket in sorted(buckets.items()):
        n = int(bucket["n"])
        kind: NodeKind = bucket["kind"]
        det: DetClass = bucket["det"]
        outputs: list[Any] = bucket["outputs"]
        errors = int(bucket["errors"])
        canon = [_canonical(o) for o in outputs]
        counts = Counter(canon)
        mode_n = counts.most_common(1)[0][1] if counts else 0
        p_mode = mode_n / n if n else 0.0
        p_lower = wilson_lower(mode_n, n)
        schema_ok = sum(_is_schema(o) for o in outputs) / n if n else 0.0
        failure_rate = errors / n if n else 0.0
        sensitive = bool(HARD_OVERRIDE.search(node_id))
        action, reasons = _decide(
            kind=kind,
            det=det,
            n=n,
            n_min=n_min,
            p_mode=p_mode,
            p_lower=p_lower,
            schema_ok=schema_ok,
            failure_rate=failure_rate,
            sensitive=sensitive,
        )
        recs.append(
            Recommendation(
                node_id=node_id,
                node_kind=kind,
                det_class=det,
                action=action,
                n=n,
                p_mode=round(p_mode, 4),
                p_mode_lower=round(p_lower, 4),
                schema_ok=round(schema_ok, 4),
                failure_rate=round(failure_rate, 4),
                estimator="observational_l0_proxy",
                reasons=tuple(reasons),
            )
        )
    return recs


def _decide(
    *,
    kind: NodeKind,
    det: DetClass,
    n: int,
    n_min: int,
    p_mode: float,
    p_lower: float,
    schema_ok: float,
    failure_rate: float,
    sensitive: bool,
) -> tuple[Action, list[str]]:
    reasons: list[str] = []
    is_llm = det in {DetClass.LLM, DetClass.LLM_SEEDED, DetClass.COMPOSITE} or kind in {
        NodeKind.LLM_REASONER,
        NodeKind.SUBAGENT,
    }
    is_det = det == DetClass.DETERMINISTIC or kind == NodeKind.DETERMINISTIC_TOOL

    if sensitive and is_llm:
        return Action.STRENGTHEN_SDB, [
            "hard override: commit/spend/PII/auth must stay a deterministic gate",
            "keep proposer; do not FlipToNondet a commit path",
        ]
    if sensitive and is_det and failure_rate > 0:
        return Action.STRENGTHEN_SDB, [
            "hard override: failures on a sensitive DET node harden the gate, not the model",
        ]
    if n < n_min:
        return Action.ABSTAIN, [f"n={n} < n_min={n_min}"]
    if is_llm and schema_ok >= SCHEMA_OK_MIN and p_mode >= P_MODE_MIN and p_lower >= P_MODE_MIN:
        reasons = [
            f"schema_ok={schema_ok:.2f} >= {SCHEMA_OK_MIN}",
            f"p_mode={p_mode:.2f} (wilson_lower={p_lower:.2f}) >= {P_MODE_MIN}",
        ]
        return Action.FLIP_TO_DET, reasons
    if is_det and failure_rate >= 0.30 and not sensitive:
        return Action.FLIP_TO_NONDET, [
            f"DET node failure_rate={failure_rate:.2f} >= 0.30 on unhandled tail",
            "wrap any new LLM in proposer/verifier/commit/reject",
        ]
    if is_llm and schema_ok >= SCHEMA_OK_MIN and p_mode >= P_MODE_MIN and p_lower < P_MODE_MIN:
        return Action.ABSTAIN, [
            f"p_mode point {p_mode:.2f} meets threshold but wilson_lower {p_lower:.2f} does not",
        ]
    reasons.append("no rule fired with a CI that excludes the threshold")
    return Action.ABSTAIN, reasons


def recommendations_to_dict(recs: Iterable[Recommendation]) -> dict[str, Any]:
    return {
        "disclaimer": DISCLAIMER,
        "estimator": "observational_l0_proxy",
        "canary": list(CANARY_CHECKLIST),
        "recommendations": [
            {
                "node_id": r.node_id,
                "node_kind": r.node_kind.value,
                "det_class": r.det_class.value,
                "action": r.action.value,
                "n": r.n,
                "p_mode": r.p_mode,
                "p_mode_lower": r.p_mode_lower,
                "schema_ok": r.schema_ok,
                "failure_rate": r.failure_rate,
                "estimator": r.estimator,
                "reasons": list(r.reasons),
                "disclaimer": r.disclaimer,
            }
            for r in recs
        ],
    }


def recommendations_to_markdown(recs: list[Recommendation]) -> str:
    lines = [
        "# Determinism Advisor report",
        "",
        f"> {DISCLAIMER}",
        "",
        "| node | kind | class | action | n | p_mode | p_mode_lo | schema_ok | fail |",
        "|---|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in recs:
        lines.append(
            f"| {r.node_id} | {r.node_kind.value} | {r.det_class.value} | "
            f"{r.action.value} | {r.n} | {r.p_mode:.2f} | {r.p_mode_lower:.2f} | "
            f"{r.schema_ok:.2f} | {r.failure_rate:.2f} |"
        )
    lines.extend(["", "## Reasons", ""])
    for r in recs:
        lines.append(f"### {r.node_id} — {r.action.value}")
        for reason in r.reasons:
            lines.append(f"- {reason}")
        lines.append("")
    lines.extend(["## Canary checklist", "", "Text only. Not a deploy button.", ""])
    for item in CANARY_CHECKLIST:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)
