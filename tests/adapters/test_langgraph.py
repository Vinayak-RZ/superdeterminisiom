from __future__ import annotations

from pathlib import Path

from superdeterminism.adapters.langgraph import load
from superdeterminism.models import NodeKind
from superdeterminism.pipeline import classify_span

FIXTURES = Path(__file__).parent / "fixtures"


def _classified(path: Path) -> list[tuple[str, NodeKind]]:
    traces = load(path)
    return [classify_span(span)[:2] for trace in traces for span in trace.spans]


def test_create_agent_maps_model_and_keeps_tool_child() -> None:
    pairs = _classified(FIXTURES / "create_agent_otlp.json")
    ids = [node_id for node_id, _ in pairs]
    kinds = {node_id: kind for node_id, kind in pairs}
    assert "model" in ids
    assert kinds["model"] is NodeKind.LLM_REASONER
    assert kinds["lookup_order"] is NodeKind.DETERMINISTIC_TOOL
    assert "__start__" not in ids
    assert "__end__" not in ids
    assert "tools" not in ids


def test_stategraph_maps_classify_and_tool() -> None:
    pairs = _classified(FIXTURES / "stategraph_otlp.json")
    kinds = {node_id: kind for node_id, kind in pairs}
    assert kinds["classify"] is NodeKind.LLM_REASONER
    assert kinds["lookup_order"] is NodeKind.DETERMINISTIC_TOOL


def test_langsmith_retriever_quirk() -> None:
    pairs = _classified(FIXTURES / "langsmith_retriever_quirk.json")
    assert pairs == [("search_kb", NodeKind.RETRIEVER)]
