from __future__ import annotations

from pathlib import Path

import pytest

from superdeterminism.adapters import AdapterError
from superdeterminism.adapters.langgraph import load as load_langgraph
from superdeterminism.adapters.maf import load as load_maf
from superdeterminism.models import NodeKind
from superdeterminism.pipeline import classify_span

FIXTURE = Path(__file__).parent / "fixtures" / "maf_otlp.json"


def test_langgraph_refuses_maf() -> None:
    with pytest.raises(AdapterError, match="MAF traces are not LangGraph"):
        load_langgraph(FIXTURE)


def test_maf_maps_native_ops() -> None:
    traces = load_maf(FIXTURE)
    pairs = [classify_span(span)[:2] for trace in traces for span in trace.spans]
    kinds = {kind for _, kind in pairs}
    assert NodeKind.SUBAGENT in kinds or NodeKind.LLM_REASONER in kinds
    assert any(node_id == "lookup_order" for node_id, _ in pairs)
