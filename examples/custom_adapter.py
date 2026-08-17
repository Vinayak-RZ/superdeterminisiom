"""House-orchestrator adapter example. Copy this file; keep load() → list[Trace]."""

from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.models import Trace
from superdeterminism.pipeline import load_traces, load_traces_path

NAME = "custom"


def load(path_or_bytes: Path | str | bytes) -> list[Trace]:
    if isinstance(path_or_bytes, bytes):
        return load_traces(json.loads(path_or_bytes.decode("utf-8")))
    return load_traces_path(Path(path_or_bytes))
