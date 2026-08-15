from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.models import Action, DetClass, NodeKind, Span, Trace
from superdeterminism.pipeline import (
    classify_span,
    load_traces,
    recommend_traces,
    wilson_lower,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _repeat_trace(template: dict, n: int, *, mutate=None) -> dict:
    traces = []
    for i in range(n):
        raw = json.loads(json.dumps(template["traces"][0]))
        if mutate:
            mutate(raw, i)
        traces.append(raw)
    return {"traces": traces}


def test_classify_chat_and_tool() -> None:
    chat = Span(
        name="chat gpt-4",
        attributes={"gen_ai.operation.name": "chat"},
    )
    tool = Span(
        name="execute_tool lookup_order",
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "lookup_order",
        },
    )
    node, kind, det = classify_span(chat)
    assert kind is NodeKind.LLM_REASONER
    assert det is DetClass.LLM
    node, kind, det = classify_span(tool)
    assert node == "lookup_order"
    assert kind is NodeKind.DETERMINISTIC_TOOL


def test_load_otlp() -> None:
    payload = {
        "resourceSpans": [
            {
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "name": "chat gpt-4",
                                "attributes": [
                                    {
                                        "key": "gen_ai.operation.name",
                                        "value": {"stringValue": "chat"},
                                    }
                                ],
                            }
                        ]
                    }
                ]
            }
        ]
    }
    traces = load_traces(payload)
    assert len(traces) == 1
    assert traces[0].spans[0].attributes["gen_ai.operation.name"] == "chat"


def test_flip_to_det_when_stable_schema() -> None:
    template = json.loads((FIXTURES / "advisor_stable_llm.json").read_text())
    traces = load_traces(_repeat_trace(template, 40))
    recs = recommend_traces(traces, n_min=30)
    classify = next(r for r in recs if r.node_id == "classify")
    assert classify.action is Action.FLIP_TO_DET
    assert classify.schema_ok >= 0.8
    assert classify.p_mode >= 0.7


def test_abstain_when_n_below_min() -> None:
    template = json.loads((FIXTURES / "advisor_stable_llm.json").read_text())
    traces = load_traces(_repeat_trace(template, 5))
    recs = recommend_traces(traces, n_min=30)
    assert recs[0].action is Action.ABSTAIN
    assert "n_min" in recs[0].reasons[0]


def test_strengthen_sdb_on_sensitive_llm() -> None:
    span = Span(
        name="chat",
        attributes={
            "gen_ai.operation.name": "chat",
            "langgraph_node": "issue_refund",
        },
        output={"ok": True},
    )
    recs = recommend_traces([Trace(spans=[span] * 40)], n_min=30)
    assert recs[0].action is Action.STRENGTHEN_SDB


def test_flip_to_nondet_on_failing_tool() -> None:
    span = Span(
        name="execute_tool parse_fields",
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "parse_fields",
        },
        output="nope",
        error=True,
    )
    recs = recommend_traces([Trace(spans=[span] * 40)], n_min=30)
    assert recs[0].action is Action.FLIP_TO_NONDET


def test_wilson_lower_is_below_phat() -> None:
    assert 0 < wilson_lower(21, 30) < 21 / 30
