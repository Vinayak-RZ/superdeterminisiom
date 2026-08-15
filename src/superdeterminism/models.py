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
    FLIP_TO_WORKFLOW = "FlipToWorkflow"
    FLIP_TO_SUBAGENT = "FlipToSubagent"
    FLIP_TO_ROUTER = "FlipToRouter"
    STRENGTHEN_SDB = "STRENGTHEN_SDB"
    BOUND_ORCHESTRATOR = "BoundOrchestrator"
    STRENGTHEN_ORCHESTRATOR = "StrengthenOrchestrator"
    FLIP_ORCHESTRATOR_TO_CODE = "FlipOrchestratorToCode"
    COLLAPSE_ORCHESTRATOR = "CollapseOrchestrator"
    ABSTAIN = "ABSTAIN"


class OrchestratorKind(str, Enum):
    CODE_WORKFLOW = "code_workflow"
    LLM_SUPERVISOR = "llm_supervisor"
    UNKNOWN = "unknown"


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
    from_kind: str = ""
    to_kind: str = ""
    p_path: float = 0.0
    p_path_lower: float = 0.0
    p_next: float = 0.0
    p_next_lower: float = 0.0
    disclaimer: str = "simulation != production; canary is confirmatory"


@dataclass(frozen=True)
class OrchestratorReport:
    node_id: str | None
    kind: OrchestratorKind
    action: Action
    n: int
    hops: float
    fan_out: int
    revisit_rate: float
    p_next: float
    p_next_lower: float
    p_path: float
    p_path_lower: float
    token_share: float
    hits_sensitive_ungated: bool
    estimator: str
    reasons: tuple[str, ...]
    disclaimer: str = "simulation != production; canary is confirmatory"
