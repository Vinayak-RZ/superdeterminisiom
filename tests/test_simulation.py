from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.cli import main
from superdeterminism.models import Action, Span, Trace
from superdeterminism.pipeline import recommend_full
from superdeterminism.simulation import census_paths, simulate_traces


def _chat(node: str, output) -> Span:
    return Span(
        name=f"chat {node}",
        attributes={"gen_ai.operation.name": "chat", "langgraph_node": node},
        output=output,
        tokens=1,
    )


def _tool(node: str) -> Span:
    return Span(
        name=f"execute_tool {node}",
        attributes={"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": node},
        output={"ok": True},
    )


def test_census_ranks_common_and_rare_paths() -> None:
    traces = [
        Trace(spans=[_chat("a", "x"), _tool("b")])
        for _ in range(20)
    ] + [
        Trace(spans=[_chat("a", "y"), _tool("c")])
        for _ in range(5)
    ]
    census = census_paths(traces)
    assert census.n_traces == 25
    assert census.unique_paths == 2
    assert census.mode_path == ("a", "b")
    assert census.paths[0].n == 20
    assert census.rare_paths == 0
    assert any(t.src == "a" and t.dst == "b" for t in census.transitions)


def test_router_splice_collapses_divergent_suffix() -> None:
    traces = [
        Trace(spans=[_chat("route", f"i-{i}"), _tool("billing")])
        for i in range(27)
    ] + [
        Trace(spans=[_chat("route", f"j-{i}"), _tool("other")])
        for i in range(3)
    ]
    recs, orch = recommend_full(traces, n_min=30)
    route = next(r for r in recs if r.node_id == "route")
    assert route.action is Action.FLIP_TO_ROUTER
    sim = simulate_traces(traces, recs, orch)
    cf = next(c for c in sim.counterfactuals if c.node_id == "route")
    assert cf.unique_paths_observed == 2
    assert cf.unique_paths_counterfactual == 1
    assert cf.counterfactual_mode == ("route", "billing")
    assert cf.mass_on_mode_delta > 0


def test_workflow_splice_collapses_to_modal_path() -> None:
    traces = [
        Trace(
            spans=[
                _chat("triage", f"t-{i}"),
                _tool("lookup_order"),
                _chat("reply", f"r-{i}"),
            ]
        )
        for i in range(30)
    ]
    recs, orch = recommend_full(traces, n_min=30)
    sim = simulate_traces(traces, recs, orch)
    assert any(c.action == Action.FLIP_TO_WORKFLOW.value for c in sim.counterfactuals)
    wf = next(c for c in sim.counterfactuals if c.action == Action.FLIP_TO_WORKFLOW.value)
    assert wf.unique_paths_counterfactual == 1


def test_bound_splice_drops_revisits() -> None:
    traces = [
        Trace(
            spans=[
                Span(
                    name="invoke_agent supervisor",
                    attributes={
                        "gen_ai.operation.name": "invoke_agent",
                        "gen_ai.agent.name": "supervisor",
                    },
                    output={"next": "research"},
                    tokens=4,
                ),
                _tool("research"),
                _tool("research"),
                _tool("research"),
            ]
        )
        for _ in range(30)
    ]
    recs, orch = recommend_full(traces, n_min=30)
    assert orch.action is Action.BOUND_ORCHESTRATOR
    sim = simulate_traces(traces, recs, orch)
    bound = next(c for c in sim.counterfactuals if c.action == Action.BOUND_ORCHESTRATOR.value)
    assert "research" in bound.counterfactual_mode
    assert bound.counterfactual_mode.count("research") == 1


def _hub(node: str = "supervisor") -> Span:
    return Span(
        name=f"invoke_agent {node}",
        attributes={
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": node,
        },
        output={"next": "research"},
        tokens=4,
    )


def test_decision_points_and_insights_explain_splits() -> None:
    traces = [
        Trace(spans=[_chat("a", "x"), _tool("b")])
        for _ in range(20)
    ] + [
        Trace(spans=[_chat("a", "y"), _tool("c")])
        for _ in range(5)
    ]
    census = census_paths(traces)
    split = next(d for d in census.decision_points if d.node_id == "a")
    assert split.fan_out == 2
    assert split.modal_next == "b"
    assert split.visit_rate == 1.0
    assert any(p.nodes == ("a",) and p.suffix_fan_out == 2 for p in census.prefixes)
    sim = simulate_traces(traces)
    kinds = {i.kind for i in sim.insights}
    assert "open_split" in kinds or "stable_split" in kinds
    assert "bottleneck_split" in kinds


def test_dominant_path_insight_and_ranked_workflow() -> None:
    traces = [
        Trace(
            spans=[
                _chat("triage", f"t-{i}"),
                _tool("lookup_order"),
                _chat("reply", f"r-{i}"),
            ]
        )
        for i in range(30)
    ]
    sim = simulate_traces(traces)
    assert any(i.kind == "dominant_path" for i in sim.insights)
    assert sim.ranked
    assert sim.ranked[0].action == Action.FLIP_TO_WORKFLOW.value
    assert sim.ranked[0].entropy_delta <= 0


def test_cassette_miss_marks_router_splice_invalid() -> None:
    traces = [
        Trace(spans=[_tool("start"), _chat("route", f"i-{i}"), _tool("billing")])
        for i in range(27)
    ] + [
        Trace(spans=[_tool("alt"), _chat("route", f"j-{i}"), _tool("other")])
        for i in range(3)
    ]
    recs, orch = recommend_full(traces, n_min=30)
    route = next(r for r in recs if r.node_id == "route")
    assert route.action is Action.FLIP_TO_ROUTER
    sim = simulate_traces(traces, recs, orch)
    cf = next(c for c in sim.counterfactuals if c.node_id == "route")
    assert cf.valid is False
    assert any("cassette miss" in r for r in cf.reasons)
    assert all(row.node_id != "route" for row in sim.ranked)


def test_nondet_splice_cannot_invent_tail() -> None:
    traces = [
        Trace(
            spans=[
                Span(
                    name="execute_tool lookup",
                    attributes={
                        "gen_ai.operation.name": "execute_tool",
                        "gen_ai.tool.name": "lookup",
                    },
                    output={"ok": i >= 10},
                    error=i < 10,
                )
            ]
        )
        for i in range(30)
    ]
    recs, orch = recommend_full(traces, n_min=30)
    lookup = next(r for r in recs if r.node_id == "lookup")
    assert lookup.action is Action.FLIP_TO_NONDET
    sim = simulate_traces(traces, recs, orch)
    cf = next(c for c in sim.counterfactuals if c.action == Action.FLIP_TO_NONDET.value)
    assert cf.valid is False


def test_strengthen_inserts_gate() -> None:
    traces = [
        Trace(spans=[_chat("issue_refund", {"amount": 1})])
        for _ in range(30)
    ]
    recs, orch = recommend_full(traces, n_min=30)
    refund = next(r for r in recs if r.node_id == "issue_refund")
    assert refund.action is Action.STRENGTHEN_SDB
    sim = simulate_traces(traces, recs, orch)
    cf = next(c for c in sim.counterfactuals if c.action == Action.STRENGTHEN_SDB.value)
    assert cf.valid is True
    assert cf.counterfactual_mode == ("issue_refund_gate", "issue_refund")


def test_collapse_keeps_first_hub_visit() -> None:
    traces = [
        Trace(spans=[_hub(), _tool("worker_a"), _hub(), _tool("worker_b")])
        for _ in range(30)
    ]
    recs, orch = recommend_full(traces, n_min=30)
    assert orch.action is Action.COLLAPSE_ORCHESTRATOR
    sim = simulate_traces(traces, recs, orch)
    cf = next(c for c in sim.counterfactuals if c.action == Action.COLLAPSE_ORCHESTRATOR.value)
    assert cf.counterfactual_mode == ("supervisor", "worker_a", "worker_b")
    assert cf.counterfactual_mode.count("supervisor") == 1


def test_cli_simulate_and_recommend_include_census(tmp_path: Path, capsys) -> None:
    traces = {
        "traces": [
            {
                "spans": [
                    {
                        "name": "chat",
                        "attributes": {
                            "gen_ai.operation.name": "chat",
                            "langgraph_node": "classify",
                        },
                        "output": {"intent": "other"},
                    }
                ]
            }
        ]
        * 3
    }
    path = tmp_path / "t.json"
    path.write_text(json.dumps(traces), encoding="utf-8")
    assert main(["simulate", str(path), "--n-min", "1"]) == 0
    sim = json.loads(capsys.readouterr().out)
    assert sim["level"] == "l0_tape_splice"
    assert sim["census"]["n_traces"] == 3
    assert sim["census"]["mode_path"] == ["classify"]
    assert "decision_points" in sim["census"]
    assert "insights" in sim
    assert "ranked" in sim
    assert main(["recommend", str(path), "--n-min", "1"]) == 0
    rec = json.loads(capsys.readouterr().out)
    assert rec["simulation"]["census"]["unique_paths"] == 1
    assert "decision_points" in rec["simulation"]["census"]
