from __future__ import annotations

from pathlib import Path

from superdeterminism.adapters.langfuse import load
from superdeterminism.models import NodeKind
from superdeterminism.pipeline import classify_span

FIXTURES = Path(__file__).parent / "fixtures"


def test_langfuse_coalesce_generation_and_tool() -> None:
    traces = load(FIXTURES / "langfuse_otlp.json")
    pairs = [classify_span(span)[:2] for trace in traces for span in trace.spans]
    kinds = {node_id: kind for node_id, kind in pairs}
    assert any(kind is NodeKind.LLM_REASONER for _, kind in pairs)
    assert kinds["lookup_order"] is NodeKind.DETERMINISTIC_TOOL
    for span in traces[0].spans:
        for key in span.attributes:
            assert not key.startswith("gen_ai.") or key in {
                "gen_ai.operation.name",
                "gen_ai.tool.name",
            }
