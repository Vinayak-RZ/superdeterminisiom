from __future__ import annotations

from superdeterminism.models import Action, NodeKind, Span, Trace
from superdeterminism.pipeline import recommend_full, recommend_traces


def _chat(node: str, output, *, ns: str = "", tokens: int = 1) -> Span:
    attrs = {"gen_ai.operation.name": "chat", "langgraph_node": node}
    if ns:
        attrs["langgraph_checkpoint_ns"] = ns
    return Span(name=f"chat {node}", attributes=attrs, output=output, tokens=tokens)


def _tool(node: str, output=None, *, error: bool = False) -> Span:
    return Span(
        name=f"execute_tool {node}",
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": node,
        },
        output=output or {"ok": True},
        error=error,
    )


def _hub(node: str = "supervisor") -> Span:
    return Span(
        name=f"invoke_agent {node}",
        attributes={
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": node,
        },
        output={"next": "worker"},
        tokens=10,
    )


def _repeat(spans_fn, n: int) -> list[Trace]:
    return [Trace(spans=spans_fn(i)) for i in range(n)]


def test_flip_to_workflow_on_stable_path_unstable_output() -> None:
    traces = _repeat(
        lambda i: [
            _chat("triage", f"ticket-{i}"),
            _tool("lookup_order"),
            _chat("reply", f"thanks-{i}"),
        ],
        30,
    )
    recs = recommend_traces(traces, n_min=30)
    triage = next(r for r in recs if r.node_id == "triage")
    assert triage.action is Action.FLIP_TO_WORKFLOW
    assert triage.from_kind == NodeKind.LLM_REASONER.value
    assert triage.to_kind == NodeKind.WORKFLOW.value


def test_flip_to_subagent_on_nested_unstable_schema() -> None:
    traces = _repeat(
        lambda i: [
            _chat("extract", {"field": f"v{i}"}, ns="parent:extract"),
        ],
        30,
    )
    recs = recommend_traces(traces, n_min=30)
    extract = next(r for r in recs if r.node_id == "extract")
    assert extract.action is Action.FLIP_TO_SUBAGENT
    assert extract.to_kind == NodeKind.SUBAGENT.value


def test_flip_to_router_on_stable_next_hop() -> None:
    traces = _repeat(
        lambda i: [
            _chat("route", f"intent-{i}"),
            _tool("billing"),
        ],
        30,
    )
    recs = recommend_traces(traces, n_min=30)
    route = next(r for r in recs if r.node_id == "route")
    assert route.action is Action.FLIP_TO_ROUTER
    assert route.to_kind == NodeKind.ROUTER.value


def test_bound_orchestrator_on_revisit() -> None:
    traces = _repeat(
        lambda _i: [_hub(), _tool("research"), _tool("research"), _tool("research")],
        30,
    )
    _recs, orch = recommend_full(traces, n_min=30)
    assert orch.action is Action.BOUND_ORCHESTRATOR
    assert orch.node_id == "supervisor"


def test_flip_orchestrator_to_code_on_stable_next() -> None:
    traces = _repeat(lambda _i: [_hub(), _tool("billing")], 30)
    _recs, orch = recommend_full(traces, n_min=30)
    assert orch.action is Action.FLIP_ORCHESTRATOR_TO_CODE
    assert orch.kind.value == "llm_supervisor"


def test_collapse_orchestrator_on_stable_path_unstable_next() -> None:
    traces = _repeat(
        lambda _i: [_hub(), _tool("worker_a"), _hub(), _tool("worker_b")],
        30,
    )
    _recs, orch = recommend_full(traces, n_min=30)
    assert orch.action is Action.COLLAPSE_ORCHESTRATOR


def test_strengthen_orchestrator_ungated_refund() -> None:
    traces = _repeat(lambda _i: [_hub(), _tool("issue_refund")], 30)
    _recs, orch = recommend_full(traces, n_min=30)
    assert orch.action is Action.STRENGTHEN_ORCHESTRATOR
    assert orch.hits_sensitive_ungated is True


def test_orchestrator_abstain_without_hub() -> None:
    traces = _repeat(lambda i: [_chat("narrate", f"story-{i}")], 30)
    _recs, orch = recommend_full(traces, n_min=30)
    assert orch.action is Action.ABSTAIN


def test_flip_to_det_still_wins_on_stable_output() -> None:
    traces = _repeat(
        lambda _i: [_chat("classify", {"intent": "other"})],
        40,
    )
    recs = recommend_traces(traces, n_min=30)
    classify = next(r for r in recs if r.node_id == "classify")
    assert classify.action is Action.FLIP_TO_DET
