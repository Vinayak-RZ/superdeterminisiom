"""Identify the control-flow owner and recommend hub actions. No gen_ai.* invented."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from superdeterminism.models import (
    Action,
    DetClass,
    NodeKind,
    OrchestratorKind,
    OrchestratorReport,
    Span,
)

# ponytail: same sensitive names as pipeline; hub reaching these ungated is Strengthen
_SENSITIVE = re.compile(
    r"(refund|commit|payment|payout|auth|oauth|pii|password|secret|spend|charge)",
    re.I,
)
HOPS_BOUND = 8.0
REVISIT_MIN = 0.30
P_NEXT_MIN = 0.70
DISCLAIMER = "simulation != production; canary is confirmatory"

ClassifiedHop = tuple[str, NodeKind, DetClass, Span]


def identify_hub(
    classified: list[list[ClassifiedHop]],
) -> tuple[str | None, OrchestratorKind]:
    """At most one hub. Competing roots → (None, UNKNOWN)."""
    votes: Counter[str] = Counter()
    kinds: dict[str, OrchestratorKind] = {}
    for hops in classified:
        candidates = _hub_candidates(hops)
        if len(candidates) != 1:
            continue
        node_id, kind = candidates[0]
        votes[node_id] += 1
        kinds[node_id] = kind
    if not votes:
        return None, OrchestratorKind.UNKNOWN
    top = votes.most_common(2)
    if len(top) > 1 and top[0][1] == top[1][1]:
        return None, OrchestratorKind.UNKNOWN
    hub_id = top[0][0]
    return hub_id, kinds.get(hub_id, OrchestratorKind.UNKNOWN)


def _hub_candidates(hops: list[ClassifiedHop]) -> list[tuple[str, OrchestratorKind]]:
    found: list[tuple[str, OrchestratorKind]] = []
    seen: set[str] = set()
    for node_id, kind, det, span in hops:
        op = str(
            (span.attributes or {}).get("gen_ai.operation.name")
            or (span.attributes or {}).get("gen_ai.operation")
            or ""
        ).lower()
        name = f"{node_id} {span.name}".lower()
        is_envelope = (
            kind is NodeKind.WORKFLOW
            or op in {"invoke_workflow", "invoke_agent", "create_agent"}
            or any(tok in name for tok in ("supervisor", "kickoff", "orchestrat", "triage"))
        )
        if not is_envelope:
            continue
        ns = str((span.attributes or {}).get("langgraph_checkpoint_ns") or "")
        if ns.count(":") >= 2 or ns.count("|") >= 2:
            continue
        if node_id in seen:
            continue
        seen.add(node_id)
        hub_kind = (
            OrchestratorKind.LLM_SUPERVISOR
            if det in {DetClass.LLM, DetClass.LLM_SEEDED, DetClass.COMPOSITE}
            or kind in {NodeKind.LLM_REASONER, NodeKind.SUBAGENT}
            else OrchestratorKind.CODE_WORKFLOW
        )
        if kind is NodeKind.WORKFLOW and det is DetClass.COMPOSITE:
            hub_kind = OrchestratorKind.LLM_SUPERVISOR
        found.append((node_id, hub_kind))
    return found


def hub_metrics(
    classified: list[list[ClassifiedHop]],
    hub_id: str,
) -> dict[str, Any]:
    hop_counts: list[int] = []
    workers: set[str] = set()
    revisits = 0
    next_hops: list[str] = []
    hub_tokens = 0
    all_tokens = 0
    ungated = False
    for hops in classified:
        seq = [h[0] for h in hops]
        hub_idx = [i for i, hid in enumerate(seq) if hid == hub_id]
        hop_counts.append(len(hub_idx) or (1 if hub_id in seq else 0))
        seen_worker: set[str] = set()
        for i, (node_id, kind, _det, span) in enumerate(hops):
            all_tokens += int(span.tokens or 0)
            if node_id == hub_id:
                hub_tokens += int(span.tokens or 0)
                if i + 1 < len(hops):
                    next_hops.append(hops[i + 1][0])
                continue
            workers.add(node_id)
            if node_id in seen_worker:
                revisits += 1
            seen_worker.add(node_id)
            if _SENSITIVE.search(node_id) and kind is NodeKind.DETERMINISTIC_TOOL:
                last_hub = max(
                    (j for j, h in enumerate(hops[:i]) if h[0] == hub_id),
                    default=None,
                )
                if last_hub is not None:
                    between = hops[last_hub + 1 : i]
                    has_gate = any(
                        "gate" in p[0].lower() or p[1] is NodeKind.ROUTER for p in between
                    )
                    if not has_gate:
                        ungated = True
    n = len(classified)
    hops_mean = sum(hop_counts) / n if n else 0.0
    next_counts = Counter(next_hops)
    mode_n = next_counts.most_common(1)[0][1] if next_counts else 0
    p_next = mode_n / len(next_hops) if next_hops else 0.0
    worker_events = max(1, sum(len([h for h in hops if h[0] != hub_id]) for hops in classified))
    return {
        "hops": hops_mean,
        "fan_out": len(workers),
        "revisit_rate": revisits / worker_events,
        "p_next": p_next,
        "next_successes": mode_n,
        "next_n": len(next_hops),
        "token_share": (hub_tokens / all_tokens) if all_tokens else 0.0,
        "hits_sensitive_ungated": ungated,
    }


def decide_orchestrator(
    *,
    hub_id: str | None,
    kind: OrchestratorKind,
    n: int,
    n_min: int,
    hops: float,
    fan_out: int,
    revisit_rate: float,
    p_next: float,
    p_next_lower: float,
    p_path: float,
    p_path_lower: float,
    hits_sensitive_ungated: bool,
) -> tuple[Action, list[str]]:
    if hub_id is None:
        return Action.ABSTAIN, ["no single control-flow owner"]
    if n < n_min:
        return Action.ABSTAIN, [f"n={n} < n_min={n_min}"]
    if hits_sensitive_ungated:
        return Action.STRENGTHEN_ORCHESTRATOR, [
            "hub reaches a sensitive tool with no intervening DET gate",
            "keep the hub; add HITL / policy gate; do not FlipToNondet the hub",
        ]
    if hops >= HOPS_BOUND or revisit_rate >= REVISIT_MIN:
        return Action.BOUND_ORCHESTRATOR, [
            f"hops={hops:.2f} or revisit_rate={revisit_rate:.2f} looks unbounded",
            "add a hard step/turn/token cap in code",
        ]
    if (
        kind is OrchestratorKind.LLM_SUPERVISOR
        and p_next >= P_NEXT_MIN
        and p_next_lower >= P_NEXT_MIN
    ):
        return Action.FLIP_ORCHESTRATOR_TO_CODE, [
            f"p_next={p_next:.2f} (wilson_lower={p_next_lower:.2f}) >= {P_NEXT_MIN}",
            "replace the LLM supervisor with a code router / DAG",
        ]
    if (
        fan_out >= 2
        and p_path >= P_NEXT_MIN
        and p_path_lower >= P_NEXT_MIN
    ):
        return Action.COLLAPSE_ORCHESTRATOR, [
            f"fan_out={fan_out} and p_path={p_path:.2f} (wilson_lower={p_path_lower:.2f})",
            "no isolation win; drop to one agent + tools or a fixed workflow",
        ]
    return Action.ABSTAIN, ["no orchestrator rule fired with a CI that excludes the threshold"]


def empty_orchestrator(*, n: int, reasons: list[str]) -> OrchestratorReport:
    return OrchestratorReport(
        node_id=None,
        kind=OrchestratorKind.UNKNOWN,
        action=Action.ABSTAIN,
        n=n,
        hops=0.0,
        fan_out=0,
        revisit_rate=0.0,
        p_next=0.0,
        p_next_lower=0.0,
        p_path=0.0,
        p_path_lower=0.0,
        token_share=0.0,
        hits_sensitive_ungated=False,
        estimator="observational_l0_proxy",
        reasons=tuple(reasons),
        disclaimer=DISCLAIMER,
    )
