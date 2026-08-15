"""LangGraph / LangChain 1.x adapter. Attribute-only mapper.

ponytail: no langchain/langgraph import. Extra presence is checked in resolve().
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from superdeterminism.models import Span, Trace
from superdeterminism.pipeline import load_traces, load_traces_path

_DROP_NODES = frozenset({"__start__", "__end__"})
_MODEL_NODES = frozenset({"model", "llm_call"})


def load(path_or_bytes: Path | str | bytes) -> list[Trace]:
    traces = _ingest(path_or_bytes)
    return [Trace(spans=_map_spans(t.spans)) for t in traces]


def _ingest(path_or_bytes: Path | str | bytes) -> list[Trace]:
    if isinstance(path_or_bytes, bytes):
        return load_traces(json.loads(path_or_bytes.decode("utf-8")))
    return load_traces_path(Path(path_or_bytes))


def _map_spans(spans: list[Span]) -> list[Span]:
    out: list[Span] = []
    for span in spans:
        mapped = _map_span(span)
        if mapped is not None:
            out.append(mapped)
    return out


def _map_span(span: Span) -> Span | None:
    attrs = dict(span.attributes)
    node = str(attrs.get("langgraph_node") or "")
    if node in _DROP_NODES:
        return None
    op = str(attrs.get("gen_ai.operation.name") or attrs.get("gen_ai.operation") or "").lower()
    smith_kind = str(
        attrs.get("langsmith.span.kind") or attrs.get("span.kind") or ""
    ).lower()

    if smith_kind == "retriever":
        attrs["gen_ai.operation.name"] = "retrieval"
        return _span(span, attrs)

    # create_agent ToolNode wrapper: drop the envelope, keep execute_tool children
    if node == "tools" and op != "execute_tool":
        return None
    if node == "tools" and op == "execute_tool":
        attrs.pop("langgraph_node", None)
        return _span(span, attrs)

    # Azure / Foundry: every node is invoke_agent — remap with langgraph_node
    if op == "invoke_agent" and node in _MODEL_NODES:
        attrs["gen_ai.operation.name"] = "chat"
        return _span(span, attrs)
    if op == "invoke_agent" and node and node != "agent":
        attrs["gen_ai.operation.name"] = "chat"
        return _span(span, attrs)

    if node == "model" and op in {"", "chat"}:
        attrs["gen_ai.operation.name"] = "chat"
        return _span(span, attrs)

    ns = attrs.get("langgraph_checkpoint_ns")
    if ns and op in {"invoke_agent", "create_agent", "invoke_workflow"}:
        return _span(span, attrs)

    return _span(span, attrs) if attrs != span.attributes else span


def _span(span: Span, attrs: dict[str, Any]) -> Span:
    return Span(
        name=span.name,
        attributes=attrs,
        input=span.input,
        output=span.output,
        tokens=span.tokens,
        latency_ms=span.latency_ms,
        error=span.error,
    )
