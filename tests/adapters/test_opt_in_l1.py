from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.cli import main


def _trace(tmp_path: Path) -> Path:
    path = tmp_path / "t.json"
    path.write_text(
        json.dumps(
            {
                "traces": [
                    {
                        "spans": [
                            {
                                "name": "chat",
                                "attributes": {"gen_ai.operation.name": "chat"},
                                "output": {"intent": "other"},
                            }
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def test_without_flag_never_calls_model(tmp_path: Path, monkeypatch) -> None:
    called: list[str] = []
    monkeypatch.setattr("superdeterminism.cli.call_model", lambda prompt: called.append(prompt))
    assert main(["recommend", str(_trace(tmp_path)), "--n-min", "1"]) == 0
    assert called == []


def test_opt_in_l1_warns_and_does_not_call(tmp_path: Path, monkeypatch, capsys) -> None:
    called: list[str] = []
    monkeypatch.setattr("superdeterminism.cli.call_model", lambda prompt: called.append(prompt))
    assert main(["recommend", str(_trace(tmp_path)), "--n-min", "1", "--opt-in-l1"]) == 0
    err = capsys.readouterr().err
    assert "simulation != production" in err
    assert "not a production A/B" in err
    assert called == []
