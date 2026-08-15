"""Langfuse OTLP coalesce. Prefer existing gen_ai.*; never invent new gen_ai keys."""

from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.models import Span, Trace
from superdeterminism.pipeline import load_traces, load_traces_path

# documented Langfuse observation types → existing gen_ai.operation.name values
_TYPE_TO_OP = {
    "generation": "chat",
    "tool": "execute_tool",
    "retriever": "retrieval",
    "embedding": "embeddings",
    "agent": "invoke_agent",
    "chain": "invoke_workflow",
}


def load(path_or_bytes: Path | str | bytes) -> list[Trace]:
    traces = _ingest(path_or_bytes)
    return [Trace(spans=[_map_span(s) for s in t.spans]) for t in traces]


def _ingest(path_or_bytes: Path | str | bytes) -> list[Trace]:
    if isinstance(path_or_bytes, bytes):
        return load_traces(json.loads(path_or_bytes.decode("utf-8")))
    return load_traces_path(Path(path_or_bytes))


def _map_span(span: Span) -> Span:
    attrs = dict(span.attributes)
    op = attrs.get("gen_ai.operation.name") or attrs.get("gen_ai.operation")
    lf_type = str(attrs.get("langfuse.observation.type") or "").lower()
    if not op and lf_type in _TYPE_TO_OP:
        attrs["gen_ai.operation.name"] = _TYPE_TO_OP[lf_type]
    output = span.output
    if output is None:
        output = attrs.get("langfuse.observation.output")
    return Span(
        name=span.name,
        attributes=attrs,
        input=span.input if span.input is not None else attrs.get("langfuse.observation.input"),
        output=output,
        tokens=span.tokens,
        latency_ms=span.latency_ms,
        error=span.error,
    )
