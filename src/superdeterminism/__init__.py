"""Agnostic architecture advisor. No framework imports."""

from superdeterminism.models import (
    DetClass,
    NodeKind,
    Recommendation,
    Span,
    Trace,
)
from superdeterminism.pipeline import recommend_traces

__all__ = [
    "DetClass",
    "NodeKind",
    "Recommendation",
    "Span",
    "Trace",
    "recommend_traces",
]
__version__ = "0.1.0"
