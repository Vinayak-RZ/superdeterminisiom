from __future__ import annotations

from pathlib import Path

import pytest

from superdeterminism.adapters import AdapterError, extra_installed, resolve
from superdeterminism.adapters.crewai import load
from superdeterminism.models import NodeKind
from superdeterminism.pipeline import classify_span

FIXTURE = Path(__file__).parent / "fixtures" / "crewai_kickoff.json"


def test_crewai_kickoff_maps_to_workflow() -> None:
    traces = load(FIXTURE)
    pairs = [classify_span(span)[:2] for trace in traces for span in trace.spans]
    kinds = [kind for _, kind in pairs]
    assert NodeKind.WORKFLOW in kinds
    assert NodeKind.LLM_REASONER in kinds


def test_resolve_crewai_without_extra() -> None:
    if extra_installed("crewai"):
        pytest.skip("crewai extra is installed")
    with pytest.raises(AdapterError, match="pip install"):
        resolve("crewai")
