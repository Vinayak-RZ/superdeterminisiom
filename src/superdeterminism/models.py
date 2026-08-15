from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeKind(str, Enum):
    DETERMINISTIC_TOOL = "deterministic_tool"
    LLM_REASONER = "llm_reasoner"
    SUBAGENT = "subagent"
    ROUTER = "router"
    RETRIEVER = "retriever"
    WORKFLOW = "workflow"
    UNKNOWN = "unknown"


class DetClass(str, Enum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"
    LLM_SEEDED = "llm_seeded"
    STOCHASTIC_INDEX = "stochastic_index"
    COMPOSITE = "composite"
    EXTERNAL = "external"


class Action(str, Enum):
    FLIP_TO_DET = "FlipToDet"
    FLIP_TO_NONDET = "FlipToNondet"
    STRENGTHEN_SDB = "STRENGTHEN_SDB"
    ABSTAIN = "ABSTAIN"


@dataclass(frozen=True)
class Span:
    name: str
    attributes: dict[str, Any]
    input: Any = None
    output: Any = None
    tokens: int = 0
    latency_ms: float = 0.0
    error: bool = False


@dataclass
class Trace:
    spans: list[Span] = field(default_factory=list)


@dataclass(frozen=True)
class Recommendation:
    node_id: str
    node_kind: NodeKind
    det_class: DetClass
    action: Action
    n: int
    p_mode: float
    p_mode_lower: float
    schema_ok: float
    failure_rate: float
    estimator: str
    reasons: tuple[str, ...]
    disclaimer: str = "simulation != production; canary is confirmatory"
