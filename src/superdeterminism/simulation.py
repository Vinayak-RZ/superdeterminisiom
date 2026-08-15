"""L0 path census and tape-splice counterfactuals. Not L1. Not L2 do_policy."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable

from superdeterminism.models import Action, OrchestratorReport, Recommendation, Trace
from superdeterminism.pipeline import HARD_OVERRIDE, classify_span, wilson_lower

DISCLAIMER = "simulation != production; L0 tape splice is not a production A/B"
ESTIMATOR = "observational_l0_tape_splice"
PATH_CAP = 8
RARE_N = 1


@dataclass(frozen=True)
class PathRecord:
    nodes: tuple[str, ...]
    n: int
    p: float
    p_lower: float
    errors: int
    tokens: int


@dataclass(frozen=True)
class Transition:
    src: str
    dst: str
    n: int
    p: float


@dataclass(frozen=True)
class DecisionPoint:
    """Where observed paths actually split. Observational, not a second recommender."""

    node_id: str
    n: int
    visit_rate: float
    fan_out: int
    entropy: float
    modal_next: str | None
    p_next: float
    p_next_lower: float
    next_hops: tuple[tuple[str, int, float], ...]


@dataclass(frozen=True)
class PrefixRecord:
    nodes: tuple[str, ...]
    n: int
    p: float
    suffix_fan_out: int


@dataclass(frozen=True)
class Insight:
    kind: str
    node_id: str
    suggested_action: str
    evidence: str
    n: int
    p: float


@dataclass(frozen=True)
class RankedImprovement:
    action: str
    node_id: str
    entropy_delta: float
    mass_on_mode_delta: float
    unique_paths_counterfactual: int
    why: str


@dataclass(frozen=True)
class PathCensus:
    n_traces: int
    unique_paths: int
    entropy: float
    mode_path: tuple[str, ...]
    p_mode: float
    p_mode_lower: float
    rare_paths: int
    cyclic_traces: int
    paths: tuple[PathRecord, ...]
    transitions: tuple[Transition, ...]
    decision_points: tuple[DecisionPoint, ...] = ()
    prefixes: tuple[PrefixRecord, ...] = ()
    estimator: str = ESTIMATOR
    disclaimer: str = DISCLAIMER


@dataclass(frozen=True)
class Counterfactual:
    action: str
    node_id: str
    splice: str
    valid: bool
    reasons: tuple[str, ...]
    observed_mode: tuple[str, ...]
    counterfactual_mode: tuple[str, ...]
    p_mode_observed: float
    p_mode_counterfactual: float
    unique_paths_observed: int
    unique_paths_counterfactual: int
    mass_on_mode_delta: float
    entropy_observed: float = 0.0
    entropy_counterfactual: float = 0.0
    entropy_delta: float = 0.0
    estimator: str = ESTIMATOR


@dataclass
class SimulationReport:
    level: str = "l0_tape_splice"
    census: PathCensus | None = None
    counterfactuals: list[Counterfactual] = field(default_factory=list)
    insights: list[Insight] = field(default_factory=list)
    ranked: list[RankedImprovement] = field(default_factory=list)
    disclaimer: str = DISCLAIMER
    estimator: str = ESTIMATOR


def _seq(trace: Trace) -> tuple[str, ...]:
    return tuple(classify_span(span)[0] for span in trace.spans)


def _entropy(counts: Iterable[int], n: int) -> float:
    if n <= 0:
        return 0.0
    ent = 0.0
    for c in counts:
        if c <= 0:
            continue
        p = c / n
        ent -= p * math.log2(p)
    return round(ent, 4)


def _has_cycle(nodes: tuple[str, ...]) -> bool:
    seen: set[str] = set()
    for node in nodes:
        if node in seen:
            return True
        seen.add(node)
    return False


def census_paths(traces: list[Trace]) -> PathCensus:
    seqs = [_seq(t) for t in traces]
    n = len(seqs)
    counts: Counter[tuple[str, ...]] = Counter(seqs)
    mode = counts.most_common(1)[0][0] if counts else tuple()
    mode_n = counts[mode] if mode else 0
    p_mode = mode_n / n if n else 0.0
    err_by: dict[tuple[str, ...], int] = defaultdict(int)
    tok_by: dict[tuple[str, ...], int] = defaultdict(int)
    for trace, seq in zip(traces, seqs):
        err_by[seq] += sum(1 for s in trace.spans if s.error)
        tok_by[seq] += sum(int(s.tokens or 0) for s in trace.spans)
    records = []
    for nodes, c in counts.most_common():
        records.append(
            PathRecord(
                nodes=nodes,
                n=c,
                p=round(c / n, 4) if n else 0.0,
                p_lower=round(wilson_lower(c, n), 4),
                errors=err_by[nodes],
                tokens=tok_by[nodes],
            )
        )
    edge_n: Counter[tuple[str, str]] = Counter()
    out_n: Counter[str] = Counter()
    for seq in seqs:
        for src, dst in zip(seq, seq[1:]):
            edge_n[(src, dst)] += 1
            out_n[src] += 1
    transitions = tuple(
        Transition(
            src=src,
            dst=dst,
            n=c,
            p=round(c / out_n[src], 4) if out_n[src] else 0.0,
        )
        for (src, dst), c in edge_n.most_common()
    )
    return PathCensus(
        n_traces=n,
        unique_paths=len(counts),
        entropy=_entropy(counts.values(), n),
        mode_path=mode,
        p_mode=round(p_mode, 4),
        p_mode_lower=round(wilson_lower(mode_n, n), 4),
        rare_paths=sum(1 for c in counts.values() if c <= RARE_N),
        cyclic_traces=sum(1 for s in seqs if _has_cycle(s)),
        paths=tuple(records),
        transitions=transitions,
        decision_points=_decision_points(seqs),
        prefixes=_prefixes(seqs),
    )


def _decision_points(seqs: list[tuple[str, ...]]) -> tuple[DecisionPoint, ...]:
    n = len(seqs)
    visit: Counter[str] = Counter()
    next_n: dict[str, Counter[str]] = defaultdict(Counter)
    for seq in seqs:
        seen: set[str] = set()
        for i, src in enumerate(seq):
            if src not in seen:
                visit[src] += 1
                seen.add(src)
            if i + 1 < len(seq):
                next_n[src][seq[i + 1]] += 1
    points: list[DecisionPoint] = []
    for src, outgoing in next_n.items():
        total = sum(outgoing.values())
        modal_dst, modal_c = outgoing.most_common(1)[0]
        p_next = modal_c / total if total else 0.0
        points.append(
            DecisionPoint(
                node_id=src,
                n=visit[src],
                visit_rate=round(visit[src] / n, 4) if n else 0.0,
                fan_out=len(outgoing),
                entropy=_entropy(outgoing.values(), total),
                modal_next=modal_dst,
                p_next=round(p_next, 4),
                p_next_lower=round(wilson_lower(modal_c, total), 4),
                next_hops=tuple(
                    (dst, c, round(c / total, 4)) for dst, c in outgoing.most_common()
                ),
            )
        )
    for node, v in visit.items():
        if node in next_n:
            continue
        points.append(
            DecisionPoint(
                node_id=node,
                n=v,
                visit_rate=round(v / n, 4) if n else 0.0,
                fan_out=0,
                entropy=0.0,
                modal_next=None,
                p_next=0.0,
                p_next_lower=0.0,
                next_hops=tuple(),
            )
        )
    points.sort(key=lambda p: (-p.visit_rate, -p.entropy, p.node_id))
    return tuple(points)


def _prefixes(seqs: list[tuple[str, ...]], *, max_len: int = 4) -> tuple[PrefixRecord, ...]:
    n = len(seqs)
    pref: Counter[tuple[str, ...]] = Counter()
    tails: dict[tuple[str, ...], set[str | None]] = defaultdict(set)
    for seq in seqs:
        for length in range(1, min(len(seq), max_len) + 1):
            key = seq[:length]
            pref[key] += 1
            nxt = seq[length] if length < len(seq) else None
            tails[key].add(nxt)
    records = []
    for nodes, c in pref.most_common(20):
        if c < 2:
            continue
        records.append(
            PrefixRecord(
                nodes=nodes,
                n=c,
                p=round(c / n, 4) if n else 0.0,
                suffix_fan_out=len(tails[nodes]),
            )
        )
    return tuple(records)


def interpret_census(census: PathCensus) -> list[Insight]:
    """Observational notes. Do not override ``recommend``; they explain the tape."""
    out: list[Insight] = []
    n = census.n_traces
    if n and len(census.mode_path) >= 3 and census.p_mode_lower >= 0.70:
        out.append(
            Insight(
                kind="dominant_path",
                node_id=census.mode_path[0],
                suggested_action=Action.FLIP_TO_WORKFLOW.value,
                evidence=(
                    f"modal path p={census.p_mode:.2f} wilson_lo={census.p_mode_lower:.2f} "
                    f"len={len(census.mode_path)}"
                ),
                n=n,
                p=census.p_mode,
            )
        )
    elif n and census.p_mode >= 0.70 and census.p_mode_lower < 0.70:
        out.append(
            Insight(
                kind="dominant_path_weak",
                node_id=census.mode_path[0] if census.mode_path else "",
                suggested_action=Action.ABSTAIN.value,
                evidence="p_mode meets 0.70 but Wilson does not; do not collapse yet",
                n=n,
                p=census.p_mode,
            )
        )
    open_splits = 0
    for dp in census.decision_points:
        if dp.fan_out < 2:
            continue
        if dp.p_next_lower >= 0.70:
            out.append(
                Insight(
                    kind="stable_split",
                    node_id=dp.node_id,
                    suggested_action=Action.FLIP_TO_ROUTER.value,
                    evidence=(
                        f"fan_out={dp.fan_out} modal_next={dp.modal_next} "
                        f"p_next={dp.p_next:.2f} wilson_lo={dp.p_next_lower:.2f}"
                    ),
                    n=dp.n,
                    p=dp.p_next,
                )
            )
        elif open_splits < 5:
            open_splits += 1
            out.append(
                Insight(
                    kind="open_split",
                    node_id=dp.node_id,
                    suggested_action=Action.ABSTAIN.value,
                    evidence=(
                        f"fan_out={dp.fan_out} entropy={dp.entropy} "
                        f"p_next_lo={dp.p_next_lower:.2f}; genuine branch or under-sampled"
                    ),
                    n=dp.n,
                    p=dp.p_next,
                )
            )
        if dp.visit_rate >= 0.80 and dp.fan_out >= 2:
            out.append(
                Insight(
                    kind="bottleneck_split",
                    node_id=dp.node_id,
                    suggested_action=Action.FLIP_TO_ROUTER.value
                    if dp.p_next_lower >= 0.70
                    else Action.ABSTAIN.value,
                    evidence=f"visit_rate={dp.visit_rate:.2f}; almost every trace decides here",
                    n=dp.n,
                    p=dp.visit_rate,
                )
            )
    if n and census.cyclic_traces / n >= 0.30:
        out.append(
            Insight(
                kind="cycle",
                node_id=census.mode_path[0] if census.mode_path else "",
                suggested_action=Action.BOUND_ORCHESTRATOR.value,
                evidence=f"{census.cyclic_traces}/{n} traces revisit a node",
                n=census.cyclic_traces,
                p=round(census.cyclic_traces / n, 4),
            )
        )
    if census.rare_paths >= 3 and census.unique_paths >= 5:
        out.append(
            Insight(
                kind="long_tail",
                node_id="",
                suggested_action=Action.ABSTAIN.value,
                evidence=(
                    f"{census.rare_paths} singleton paths of {census.unique_paths}; "
                    "do not collapse to the modal workflow"
                ),
                n=census.rare_paths,
                p=round(census.rare_paths / max(census.unique_paths, 1), 4),
            )
        )
    total_err = sum(p.errors for p in census.paths)
    for path in census.paths:
        if not path.errors or not total_err or path.p > 0.30:
            continue
        if path.errors / total_err < 0.50:
            continue
        out.append(
            Insight(
                kind="error_concentrated",
                node_id=path.nodes[0] if path.nodes else "",
                suggested_action=Action.ABSTAIN.value,
                evidence=(
                    f"path {' → '.join(path.nodes)} holds {path.errors}/{total_err} "
                    f"errors at p={path.p:.2f}; do not drop it into the modal collapse"
                ),
                n=path.n,
                p=path.p,
            )
        )
    return out


def rank_improvements(cfs: Iterable[Counterfactual]) -> list[RankedImprovement]:
    """Valid splices that concentrate the path distribution, most first."""
    ranked: list[RankedImprovement] = []
    for cf in cfs:
        if not cf.valid:
            continue
        why = (
            f"entropy {cf.entropy_observed:.2f} → {cf.entropy_counterfactual:.2f}; "
            f"mode mass Δ {cf.mass_on_mode_delta:+.2f}"
        )
        ranked.append(
            RankedImprovement(
                action=cf.action,
                node_id=cf.node_id,
                entropy_delta=cf.entropy_delta,
                mass_on_mode_delta=cf.mass_on_mode_delta,
                unique_paths_counterfactual=cf.unique_paths_counterfactual,
                why=why,
            )
        )
    ranked.sort(key=lambda r: (r.entropy_delta, -r.mass_on_mode_delta, r.node_id))
    return ranked


def _modal_suffix(seqs: list[tuple[str, ...]], node_id: str) -> tuple[str, ...] | None:
    suffixes: Counter[tuple[str, ...]] = Counter()
    for seq in seqs:
        if node_id not in seq:
            continue
        i = seq.index(node_id)
        suffixes[seq[i + 1 :]] += 1
    if not suffixes:
        return None
    return suffixes.most_common(1)[0][0]


def _splice_router(seq: tuple[str, ...], node_id: str, suffix: tuple[str, ...]) -> tuple[str, ...]:
    if node_id not in seq:
        return seq
    i = seq.index(node_id)
    return seq[: i + 1] + suffix


def _drop_revisits(seq: tuple[str, ...]) -> tuple[str, ...]:
    out: list[str] = []
    prev = None
    for node in seq:
        if node == prev:
            continue
        out.append(node)
        prev = node
    return tuple(out[:PATH_CAP])


def _collapse_hub(seq: tuple[str, ...], hub_id: str) -> tuple[str, ...]:
    out: list[str] = []
    seen_hub = False
    for node in seq:
        if node == hub_id:
            if seen_hub:
                continue
            seen_hub = True
        out.append(node)
    return tuple(out)


def _insert_gate(seq: tuple[str, ...], node_id: str) -> tuple[str, ...]:
    gate = f"{node_id}_gate"
    out: list[str] = []
    for node in seq:
        if node == node_id and (not out or out[-1] != gate):
            if HARD_OVERRIDE.search(node_id):
                out.append(gate)
        out.append(node)
    return tuple(out)


def _cassette_ok(original: list[tuple[str, ...]], rewritten: list[tuple[str, ...]]) -> bool:
    """Invalid if a rewritten path was never observed (suffix miss)."""
    seen = set(original)
    return all(path in seen for path in rewritten)


def _cf_stats(
    observed: list[tuple[str, ...]],
    rewritten: list[tuple[str, ...]],
    *,
    action: str,
    node_id: str,
    splice: str,
    extra_reasons: list[str],
) -> Counterfactual:
    n = len(observed)
    obs_counts = Counter(observed)
    cf_counts = Counter(rewritten)
    obs_mode = obs_counts.most_common(1)[0][0] if obs_counts else tuple()
    cf_mode = cf_counts.most_common(1)[0][0] if cf_counts else tuple()
    p_obs = (obs_counts[obs_mode] / n) if n and obs_mode else 0.0
    p_cf = (cf_counts[cf_mode] / n) if n and cf_mode else 0.0
    valid = _cassette_ok(observed, rewritten) or action in {
        Action.FLIP_TO_WORKFLOW.value,
        Action.FLIP_TO_DET.value,
        Action.BOUND_ORCHESTRATOR.value,
        Action.COLLAPSE_ORCHESTRATOR.value,
        Action.STRENGTHEN_SDB.value,
        Action.STRENGTHEN_ORCHESTRATOR.value,
    }
    reasons = list(extra_reasons)
    if not _cassette_ok(observed, rewritten):
        if valid:
            reasons.append("splice invents a collapsed path; confirmatory canary required")
        else:
            reasons.append("cassette miss: rewritten suffix was never observed")
            valid = False
    if rewritten == observed:
        valid = False
        reasons.append("splice did not change any path")
    ent_obs = _entropy(obs_counts.values(), n)
    ent_cf = _entropy(cf_counts.values(), n)
    return Counterfactual(
        action=action,
        node_id=node_id,
        splice=splice,
        valid=valid,
        reasons=tuple(reasons) or ("L0 tape splice",),
        observed_mode=obs_mode,
        counterfactual_mode=cf_mode,
        p_mode_observed=round(p_obs, 4),
        p_mode_counterfactual=round(p_cf, 4),
        unique_paths_observed=len(obs_counts),
        unique_paths_counterfactual=len(cf_counts),
        mass_on_mode_delta=round(p_cf - p_obs, 4),
        entropy_observed=ent_obs,
        entropy_counterfactual=ent_cf,
        entropy_delta=round(ent_cf - ent_obs, 4),
    )


def counterfactuals_for(
    traces: list[Trace],
    recs: Iterable[Recommendation],
    orch: OrchestratorReport | None,
) -> list[Counterfactual]:
    seqs = [_seq(t) for t in traces]
    out: list[Counterfactual] = []
    for rec in recs:
        if rec.action is Action.ABSTAIN:
            continue
        cf = _splice_action(seqs, rec.action, rec.node_id, orch)
        if cf is not None:
            out.append(cf)
    if orch is not None and orch.action is not Action.ABSTAIN and orch.node_id:
        already = {c.node_id for c in out}
        if orch.node_id not in already:
            cf = _splice_action(seqs, orch.action, orch.node_id, orch)
            if cf is not None:
                out.append(cf)
    return out


def _splice_action(
    seqs: list[tuple[str, ...]],
    action: Action,
    node_id: str,
    orch: OrchestratorReport | None,
) -> Counterfactual | None:
    if action in {Action.FLIP_TO_ROUTER, Action.FLIP_ORCHESTRATOR_TO_CODE}:
        suffix = _modal_suffix(seqs, node_id)
        if suffix is None:
            return None
        rewritten = [_splice_router(s, node_id, suffix) for s in seqs]
        return _cf_stats(
            seqs,
            rewritten,
            action=action.value,
            node_id=node_id,
            splice="after node, attach modal observed suffix",
            extra_reasons=["L0 router splice; downstream re-decides"],
        )
    if action in {Action.FLIP_TO_WORKFLOW, Action.FLIP_TO_DET}:
        mode = Counter(seqs).most_common(1)[0][0] if seqs else tuple()
        rewritten = [mode for _ in seqs]
        return _cf_stats(
            seqs,
            rewritten,
            action=action.value,
            node_id=node_id,
            splice="collapse every trace onto the modal full path",
            extra_reasons=["predefined path; unique_paths → 1 if splice holds"],
        )
    if action is Action.BOUND_ORCHESTRATOR:
        rewritten = [_drop_revisits(s) for s in seqs]
        return _cf_stats(
            seqs,
            rewritten,
            action=action.value,
            node_id=node_id,
            splice=f"drop immediate revisits; cap length at {PATH_CAP}",
            extra_reasons=["hard bound in code, not in a prompt"],
        )
    if action is Action.COLLAPSE_ORCHESTRATOR:
        hub = node_id or (orch.node_id if orch else "")
        rewritten = [_collapse_hub(s, hub) for s in seqs]
        return _cf_stats(
            seqs,
            rewritten,
            action=action.value,
            node_id=node_id,
            splice="keep the first hub visit only",
            extra_reasons=["over-orchestration: extra hub hops removed"],
        )
    if action in {Action.STRENGTHEN_SDB, Action.STRENGTHEN_ORCHESTRATOR}:
        target = node_id
        if action is Action.STRENGTHEN_ORCHESTRATOR:
            # gate the first sensitive hop after the hub
            target = _first_sensitive(seqs) or node_id
        rewritten = [_insert_gate(s, target) for s in seqs]
        return _cf_stats(
            seqs,
            rewritten,
            action=action.value,
            node_id=target,
            splice=f"insert {target}_gate before the sensitive hop",
            extra_reasons=["HITL / policy gate; hub stays"],
        )
    if action is Action.FLIP_TO_SUBAGENT:
        return _cf_stats(
            seqs,
            list(seqs),
            action=action.value,
            node_id=node_id,
            splice="context isolation does not rewrite hop ids",
            extra_reasons=["no path-id change; isolate context only"],
        )
    if action is Action.FLIP_TO_NONDET:
        return _cf_stats(
            seqs,
            list(seqs),
            action=action.value,
            node_id=node_id,
            splice="new LLM tail is not on the tape",
            extra_reasons=["L0 cannot invent a stochastic tail; ABSTAIN on path CF"],
        )
    return None


def _first_sensitive(seqs: list[tuple[str, ...]]) -> str | None:
    for seq in seqs:
        for node in seq:
            if HARD_OVERRIDE.search(node):
                return node
    return None


def simulate_traces(
    traces: list[Trace],
    recs: Iterable[Recommendation] | None = None,
    orch: OrchestratorReport | None = None,
) -> SimulationReport:
    """Enumerate paths and L0-splice recommended flips. No network."""
    from superdeterminism.pipeline import recommend_full

    if recs is None or orch is None:
        recs, orch = recommend_full(traces)
    census = census_paths(traces)
    cfs = counterfactuals_for(traces, recs, orch)
    return SimulationReport(
        census=census,
        counterfactuals=cfs,
        insights=interpret_census(census),
        ranked=rank_improvements(cfs),
    )


def simulation_to_dict(report: SimulationReport) -> dict[str, Any]:
    census = report.census
    return {
        "level": report.level,
        "disclaimer": report.disclaimer,
        "estimator": report.estimator,
        "census": None
        if census is None
        else {
            "n_traces": census.n_traces,
            "unique_paths": census.unique_paths,
            "entropy": census.entropy,
            "mode_path": list(census.mode_path),
            "p_mode": census.p_mode,
            "p_mode_lower": census.p_mode_lower,
            "rare_paths": census.rare_paths,
            "cyclic_traces": census.cyclic_traces,
            "paths": [
                {
                    "nodes": list(p.nodes),
                    "n": p.n,
                    "p": p.p,
                    "p_lower": p.p_lower,
                    "errors": p.errors,
                    "tokens": p.tokens,
                }
                for p in census.paths
            ],
            "transitions": [
                {"src": t.src, "dst": t.dst, "n": t.n, "p": t.p}
                for t in census.transitions
            ],
            "decision_points": [
                {
                    "node_id": d.node_id,
                    "n": d.n,
                    "visit_rate": d.visit_rate,
                    "fan_out": d.fan_out,
                    "entropy": d.entropy,
                    "modal_next": d.modal_next,
                    "p_next": d.p_next,
                    "p_next_lower": d.p_next_lower,
                    "next_hops": [
                        {"dst": dst, "n": hn, "p": hp} for dst, hn, hp in d.next_hops
                    ],
                }
                for d in census.decision_points
            ],
            "prefixes": [
                {
                    "nodes": list(p.nodes),
                    "n": p.n,
                    "p": p.p,
                    "suffix_fan_out": p.suffix_fan_out,
                }
                for p in census.prefixes
            ],
        },
        "insights": [
            {
                "kind": i.kind,
                "node_id": i.node_id,
                "suggested_action": i.suggested_action,
                "evidence": i.evidence,
                "n": i.n,
                "p": i.p,
            }
            for i in report.insights
        ],
        "ranked": [
            {
                "action": r.action,
                "node_id": r.node_id,
                "entropy_delta": r.entropy_delta,
                "mass_on_mode_delta": r.mass_on_mode_delta,
                "unique_paths_counterfactual": r.unique_paths_counterfactual,
                "why": r.why,
            }
            for r in report.ranked
        ],
        "counterfactuals": [
            {
                "action": c.action,
                "node_id": c.node_id,
                "splice": c.splice,
                "valid": c.valid,
                "reasons": list(c.reasons),
                "observed_mode": list(c.observed_mode),
                "counterfactual_mode": list(c.counterfactual_mode),
                "p_mode_observed": c.p_mode_observed,
                "p_mode_counterfactual": c.p_mode_counterfactual,
                "unique_paths_observed": c.unique_paths_observed,
                "unique_paths_counterfactual": c.unique_paths_counterfactual,
                "mass_on_mode_delta": c.mass_on_mode_delta,
                "entropy_observed": c.entropy_observed,
                "entropy_counterfactual": c.entropy_counterfactual,
                "entropy_delta": c.entropy_delta,
                "estimator": c.estimator,
            }
            for c in report.counterfactuals
        ],
    }


def simulation_to_markdown(report: SimulationReport) -> str:
    census = report.census
    lines = [
        "# Architecture Advisor simulation (L0)",
        "",
        f"> {report.disclaimer}",
        "",
    ]
    if census is None:
        return "\n".join(lines)
    lines.extend(
        [
            "## Path census",
            "",
            f"- traces: {census.n_traces}",
            f"- unique paths: {census.unique_paths}",
            f"- entropy (bits): {census.entropy}",
            f"- modal path: `{' → '.join(census.mode_path) or '(empty)'}` "
            f"(p={census.p_mode:.2f}, wilson_lo={census.p_mode_lower:.2f})",
            f"- rare paths (n=1): {census.rare_paths}",
            f"- cyclic traces: {census.cyclic_traces}",
            "",
            "| n | p | p_lo | errors | path |",
            "|---:|---:|---:|---:|---|",
        ]
    )
    for p in census.paths[:20]:
        lines.append(
            f"| {p.n} | {p.p:.2f} | {p.p_lower:.2f} | {p.errors} | "
            f"{' → '.join(p.nodes)} |"
        )
    if census.transitions:
        lines.extend(["", "## Transitions", "", "| from | to | n | p |", "|---|---|---:|---:|"])
        for t in census.transitions[:30]:
            lines.append(f"| {t.src} | {t.dst} | {t.n} | {t.p:.2f} |")
    splits = [d for d in census.decision_points if d.fan_out >= 2]
    if splits:
        lines.extend(
            [
                "",
                "## Decision points",
                "",
                "| node | visit | fan_out | H | modal next | p_next | p_lo |",
                "|---|---:|---:|---:|---|---:|---:|",
            ]
        )
        for d in splits[:20]:
            lines.append(
                f"| {d.node_id} | {d.visit_rate:.2f} | {d.fan_out} | {d.entropy:.2f} | "
                f"{d.modal_next or ''} | {d.p_next:.2f} | {d.p_next_lower:.2f} |"
            )
    if report.insights:
        lines.extend(["", "## Architecture notes (observational)", ""])
        for insight in report.insights:
            loc = f" `{insight.node_id}`" if insight.node_id else ""
            lines.append(
                f"- **{insight.kind}**{loc} → `{insight.suggested_action}` — {insight.evidence}"
            )
    if report.ranked:
        lines.extend(
            [
                "",
                "## Ranked L0 improvements",
                "",
                "> Valid splices only. Ranking is observational; not a production A/B.",
                "",
            ]
        )
        for i, row in enumerate(report.ranked, 1):
            lines.append(
                f"{i}. `{row.node_id}` **{row.action}** — {row.why}"
            )
    if report.counterfactuals:
        lines.extend(["", "## Counterfactual splices", ""])
        for c in report.counterfactuals:
            lines.append(f"### {c.node_id} — {c.action}")
            lines.append(f"- splice: {c.splice}")
            lines.append(f"- valid: {c.valid}")
            lines.append(
                f"- unique paths {c.unique_paths_observed} → {c.unique_paths_counterfactual}"
            )
            lines.append(
                f"- entropy {c.entropy_observed:.2f} → {c.entropy_counterfactual:.2f} "
                f"(Δ {c.entropy_delta:+.2f})"
            )
            lines.append(
                f"- mass on mode {c.p_mode_observed:.2f} → {c.p_mode_counterfactual:.2f} "
                f"(Δ {c.mass_on_mode_delta:+.2f})"
            )
            lines.append(f"- observed mode: `{' → '.join(c.observed_mode)}`")
            lines.append(f"- counterfactual mode: `{' → '.join(c.counterfactual_mode)}`")
            for reason in c.reasons:
                lines.append(f"- {reason}")
            lines.append("")
    return "\n".join(lines)
