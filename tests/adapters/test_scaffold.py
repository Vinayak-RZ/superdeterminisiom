from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.cli import main


def _report(*recs: dict) -> dict:
    return {
        "disclaimer": "simulation != production; canary is confirmatory",
        "estimator": "observational_l0_proxy",
        "recommendations": list(recs),
    }


def test_scaffold_writes_out_only_and_keeps_node_name(tmp_path: Path) -> None:
    graph = tmp_path / "graph.py"
    original = "builder.add_node('classify', llm_classify)\n"
    graph.write_text(original, encoding="utf-8")
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            _report(
                {
                    "node_id": "classify",
                    "action": "FlipToDet",
                    "reasons": ["schema_ok high"],
                }
            )
        ),
        encoding="utf-8",
    )
    out = tmp_path / "scaffold" / "RUN"
    assert main(["scaffold", str(report_path), "--out", str(out)]) == 0
    assert graph.read_text(encoding="utf-8") == original
    report_md = (out / "REPORT.md").read_text(encoding="utf-8")
    assert "## Canary checklist" in report_md
    assert "Not a deploy button" in report_md
    assert (out / "WIRING.md").is_file()
    diff = (out / "patches" / "classify.diff").read_text(encoding="utf-8")
    assert 'add_node("classify"' in diff
    assert "create_react_agent" not in diff


def test_scaffold_abstain_has_no_patches(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            _report(
                {
                    "node_id": "classify",
                    "action": "ABSTAIN",
                    "reasons": ["n=1 < n_min=30"],
                }
            )
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    assert main(["scaffold", str(report_path), "--out", str(out)]) == 0
    assert (out / "REPORT.md").is_file()
    assert not (out / "patches").exists()


def test_scaffold_refuses_send(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            _report(
                {
                    "node_id": "fanout",
                    "action": "FlipToNondet",
                    "reasons": ["uses Send for map-reduce"],
                }
            )
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    assert main(["scaffold", str(report_path), "--out", str(out)]) == 0
    assert not (out / "patches").exists()
