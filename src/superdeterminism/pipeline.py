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
    OrchestratorReport,
    Recommendation,
    Span,
    Trace,
)
from superdeterminism.orchestrator import (
    decide_orchestrator,
    empty_orchestrator,
    hub_metrics,
    identify_hub,
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


def _to_kind(action: Action, current: NodeKind) -> str:
    return {
        Action.FLIP_TO_DET: NodeKind.DETERMINISTIC_TOOL.value,
        Action.FLIP_TO_NONDET: NodeKind.LLM_REASONER.value,
        Action.FLIP_TO_WORKFLOW: NodeKind.WORKFLOW.value,
        Action.FLIP_TO_SUBAGENT: NodeKind.SUBAGENT.value,
        Action.FLIP_TO_ROUTER: NodeKind.ROUTER.value,
    }.get(action, current.value)


def _is_nested(span: Span) -> bool:
    ns = str((span.attributes or {}).get("langgraph_checkpoint_ns") or "")
    return ns.count(":") >= 1 or ns.count("|") >= 1 or bool(
        (span.attributes or {}).get("advisor.nested")
    )


def recommend_traces(
    traces: list[Trace],
    *,
    n_min: int = N_MIN_DEFAULT,
) -> list[Recommendation]:
    """L0 / observational recommend. Estimator is proxy, not L2 do_policy."""
    recs, _orch = recommend_full(traces, n_min=n_min)
    return recs


def recommend_full(
    traces: list[Trace],
    *,
    n_min: int = N_MIN_DEFAULT,
) -> tuple[list[Recommendation], OrchestratorReport]:
    classified: list[list[tuple[str, NodeKind, DetClass, Span]]] = []
    buckets: dict[str, dict[str, Any]] = {}
    nexts: dict[str, list[str]] = defaultdict(list)
    paths: list[str] = []
    for trace in traces:
        hops: list[tuple[str, NodeKind, DetClass, Span]] = []
        for span in trace.spans:
            node_id, kind, det = classify_span(span)
            hops.append((node_id, kind, det, span))
            bucket = buckets.setdefault(
                node_id,
                {
                    "kind": kind,
                    "det": det,
                    "outputs": [],
                    "errors": 0,
                    "n": 0,
                    "nested": False,
                },
            )
            bucket["n"] += 1
            bucket["outputs"].append(span.output)
            bucket["errors"] += int(span.error)
            bucket["nested"] = bucket["nested"] or _is_nested(span)
            # ponytail: last-write kind/det; mixed ops on one name need P1 split
            bucket["kind"] = kind
            bucket["det"] = det
        classified.append(hops)
        seq = [h[0] for h in hops]
        paths.append(_canonical(seq))
        for i, (node_id, _k, _d, _s) in enumerate(hops[:-1]):
            nexts[node_id].append(hops[i + 1][0])

    path_counts = Counter(paths)
    path_mode_n = path_counts.most_common(1)[0][1] if path_counts else 0
    n_traces = len(traces)
    p_path = path_mode_n / n_traces if n_traces else 0.0
    p_path_lower = wilson_lower(path_mode_n, n_traces)
    path_len = 0
    if path_counts:
        mode_path = path_counts.most_common(1)[0][0]
        try:
            path_len = len(json.loads(mode_path))
        except (json.JSONDecodeError, TypeError):
            path_len = 0

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
        nxt = nexts.get(node_id) or []
        nxt_counts = Counter(nxt)
        nxt_mode = nxt_counts.most_common(1)[0][1] if nxt_counts else 0
        p_next = nxt_mode / len(nxt) if nxt else 0.0
        p_next_lower = wilson_lower(nxt_mode, len(nxt)) if nxt else 0.0
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
            p_path=p_path,
            p_path_lower=p_path_lower,
            path_len=path_len,
            p_next=p_next,
            p_next_lower=p_next_lower,
            nested=bool(bucket["nested"]),
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
                from_kind=kind.value,
                to_kind=_to_kind(action, kind),
                p_path=round(p_path, 4),
                p_path_lower=round(p_path_lower, 4),
                p_next=round(p_next, 4),
                p_next_lower=round(p_next_lower, 4),
            )
        )
    orch = _orchestrator_report(
        classified,
        n_min=n_min,
        p_path=p_path,
        p_path_lower=p_path_lower,
    )
    return recs, orch


def _orchestrator_report(
    classified: list[list[tuple[str, NodeKind, DetClass, Span]]],
    *,
    n_min: int,
    p_path: float,
    p_path_lower: float,
) -> OrchestratorReport:
    n = len(classified)
    hub_id, kind = identify_hub(classified)
    if hub_id is None:
        return empty_orchestrator(n=n, reasons=["no single control-flow owner"])
    metrics = hub_metrics(classified, hub_id)
    p_next = float(metrics["p_next"])
    p_next_lower = wilson_lower(int(metrics["next_successes"]), int(metrics["next_n"]))
    action, reasons = decide_orchestrator(
        hub_id=hub_id,
        kind=kind,
        n=n,
        n_min=n_min,
        hops=float(metrics["hops"]),
        fan_out=int(metrics["fan_out"]),
        revisit_rate=float(metrics["revisit_rate"]),
        p_next=p_next,
        p_next_lower=p_next_lower,
        p_path=p_path,
        p_path_lower=p_path_lower,
        hits_sensitive_ungated=bool(metrics["hits_sensitive_ungated"]),
    )
    return OrchestratorReport(
        node_id=hub_id,
        kind=kind,
        action=action,
        n=n,
        hops=round(float(metrics["hops"]), 4),
        fan_out=int(metrics["fan_out"]),
        revisit_rate=round(float(metrics["revisit_rate"]), 4),
        p_next=round(p_next, 4),
        p_next_lower=round(p_next_lower, 4),
        p_path=round(p_path, 4),
        p_path_lower=round(p_path_lower, 4),
        token_share=round(float(metrics["token_share"]), 4),
        hits_sensitive_ungated=bool(metrics["hits_sensitive_ungated"]),
        estimator="observational_l0_proxy",
        reasons=tuple(reasons),
    )


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
    p_path: float = 0.0,
    p_path_lower: float = 0.0,
    path_len: int = 0,
    p_next: float = 0.0,
    p_next_lower: float = 0.0,
    nested: bool = False,
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
    if (
        is_llm
        and path_len >= 3
        and p_path >= P_MODE_MIN
        and p_path_lower >= P_MODE_MIN
        and p_mode < P_MODE_MIN
    ):
        return Action.FLIP_TO_WORKFLOW, [
            f"p_path={p_path:.2f} (wilson_lower={p_path_lower:.2f}) >= {P_MODE_MIN}",
            f"path_len={path_len} >= 3; output not mode-stable so FlipToDet is not the lower rung",
        ]
    if is_llm and nested and schema_ok >= SCHEMA_OK_MIN and p_mode < P_MODE_MIN:
        return Action.FLIP_TO_SUBAGENT, [
            "nested checkpoint ns with structured return and unstable output",
            "isolate the hop; child returns one structured result",
        ]
    if is_llm and p_next >= P_MODE_MIN and p_next_lower >= P_MODE_MIN:
        return Action.FLIP_TO_ROUTER, [
            f"p_next={p_next:.2f} (wilson_lower={p_next_lower:.2f}) >= {P_MODE_MIN}",
            "lift the model-chosen branch into a classifier / code edge",
        ]
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


def _orchestrator_to_dict(orch: OrchestratorReport | None) -> dict[str, Any]:
    if orch is None:
        return {
            "node_id": None,
            "kind": "unknown",
            "action": Action.ABSTAIN.value,
            "reasons": ["orchestrator not computed"],
        }
    return {
        "node_id": orch.node_id,
        "kind": orch.kind.value,
        "action": orch.action.value,
        "n": orch.n,
        "hops": orch.hops,
        "fan_out": orch.fan_out,
        "revisit_rate": orch.revisit_rate,
        "p_next": orch.p_next,
        "p_next_lower": orch.p_next_lower,
        "p_path": orch.p_path,
        "p_path_lower": orch.p_path_lower,
        "token_share": orch.token_share,
        "hits_sensitive_ungated": orch.hits_sensitive_ungated,
        "estimator": orch.estimator,
        "reasons": list(orch.reasons),
        "disclaimer": orch.disclaimer,
    }


def recommendations_to_dict(
    recs: Iterable[Recommendation],
    orchestrator: OrchestratorReport | None = None,
    simulation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "disclaimer": DISCLAIMER,
        "estimator": "observational_l0_proxy",
        "canary": list(CANARY_CHECKLIST),
        "orchestrator": _orchestrator_to_dict(orchestrator),
        "recommendations": [
            {
                "node_id": r.node_id,
                "node_kind": r.node_kind.value,
                "det_class": r.det_class.value,
                "from_kind": r.from_kind or r.node_kind.value,
                "to_kind": r.to_kind or r.node_kind.value,
                "action": r.action.value,
                "n": r.n,
                "p_mode": r.p_mode,
                "p_mode_lower": r.p_mode_lower,
                "p_path": r.p_path,
                "p_path_lower": r.p_path_lower,
                "p_next": r.p_next,
                "p_next_lower": r.p_next_lower,
                "schema_ok": r.schema_ok,
                "failure_rate": r.failure_rate,
                "estimator": r.estimator,
                "reasons": list(r.reasons),
                "disclaimer": r.disclaimer,
            }
            for r in recs
        ],
    }
    if simulation is not None:
        payload["simulation"] = simulation
    return payload


def recommendations_to_markdown(
    recs: list[Recommendation],
    orchestrator: OrchestratorReport | None = None,
    simulation_md: str | None = None,
) -> str:
    lines = [
        "# Architecture Advisor report",
        "",
        f"> {DISCLAIMER}",
        "",
        "| node | kind | to | action | n | p_mode | p_path | p_next | schema_ok | fail |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in recs:
        lines.append(
            f"| {r.node_id} | {r.from_kind or r.node_kind.value} | {r.to_kind} | "
            f"{r.action.value} | {r.n} | {r.p_mode:.2f} | {r.p_path:.2f} | "
            f"{r.p_next:.2f} | {r.schema_ok:.2f} | {r.failure_rate:.2f} |"
        )
    if orchestrator is not None:
        lines.extend(
            [
                "",
                "## Orchestrator",
                "",
                f"- id: `{orchestrator.node_id}`",
                f"- kind: {orchestrator.kind.value}",
                f"- action: **{orchestrator.action.value}**",
                f"- hops: {orchestrator.hops:.2f} fan_out: {orchestrator.fan_out} "
                f"revisit: {orchestrator.revisit_rate:.2f} p_next: {orchestrator.p_next:.2f}",
            ]
        )
        for reason in orchestrator.reasons:
            lines.append(f"- {reason}")
    lines.extend(["", "## Reasons", ""])
    for r in recs:
        lines.append(f"### {r.node_id} — {r.action.value}")
        for reason in r.reasons:
            lines.append(f"- {reason}")
        lines.append("")
    if simulation_md:
        lines.extend(["", simulation_md.rstrip(), ""])
    lines.extend(["## Canary checklist", "", "Text only. Not a deploy button.", ""])
    for item in CANARY_CHECKLIST:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)
