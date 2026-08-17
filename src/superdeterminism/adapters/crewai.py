"""CrewAI mapper. Role/task loop, not StateGraph. kickoff → workflow."""

from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.models import Span, Trace
from superdeterminism.pipeline import load_traces, load_traces_path

NAME = "crewai"


def load(path_or_bytes: Path | str | bytes) -> list[Trace]:
    traces = _ingest(path_or_bytes)
    return [Trace(spans=[_map_span(s) for s in t.spans]) for t in traces]


def _ingest(path_or_bytes: Path | str | bytes) -> list[Trace]:
    if isinstance(path_or_bytes, bytes):
        return load_traces(json.loads(path_or_bytes.decode("utf-8")))
    return load_traces_path(Path(path_or_bytes))


def _map_span(span: Span) -> Span:
    attrs = dict(span.attributes)
    op = str(attrs.get("gen_ai.operation.name") or attrs.get("gen_ai.operation") or "").lower()
    name = span.name.lower()
    if op in {"kickoff", "crew.kickoff"} or "kickoff" in name or attrs.get("crewai.kickoff"):
        attrs["gen_ai.operation.name"] = "invoke_workflow"
    return Span(
        name=span.name,
        attributes=attrs,
        input=span.input,
        output=span.output,
        tokens=span.tokens,
        latency_ms=span.latency_ms,
        error=span.error,
    )
