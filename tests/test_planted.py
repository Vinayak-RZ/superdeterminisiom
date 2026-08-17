from __future__ import annotations

from pathlib import Path

from superdeterminism.models import Action
from superdeterminism.pipeline import load_traces_path, recommend_traces

FIXTURES = Path(__file__).parent / "fixtures"


def test_planted_det_flips_to_det() -> None:
    traces = load_traces_path(FIXTURES / "planted_det.json")
    recs = recommend_traces(traces, n_min=30)
    assert recs
    assert recs[0].action is Action.FLIP_TO_DET
    assert recs[0].node_id == "classify"


def test_planted_open_ended_abstains() -> None:
    traces = load_traces_path(FIXTURES / "planted_open_ended.json")
    recs = recommend_traces(traces, n_min=30)
    assert recs
    assert recs[0].action is Action.ABSTAIN
    assert recs[0].node_id == "narrate"
