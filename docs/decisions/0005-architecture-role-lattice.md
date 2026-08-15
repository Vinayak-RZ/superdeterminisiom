# ADR 0005 — Architecture role lattice and orchestrator object

- **Status:** accepted
- **Date:** 2026-08-15
- **Index:** [DECISIONS.md](../../DECISIONS.md)

## Context

P0–P2 recommend only FlipToDet / FlipToNondet / STRENGTHEN_SDB / ABSTAIN. The domain model already has `workflow`, `subagent`, `router`. Teams need evidence for workflow vs subagent vs tool vs router, and for whether the *orchestrator* should be bounded, collapsed, or turned into a code path.

## Alternatives

- Stay tool-vs-LLM only
- Become a static / interview architecture advisor (AgentLint / arch-advisor)
- Search a new graph from scratch (MaAS / AFlow)
- Widen re-typing on ingested graphs; treat the orchestrator as a graph-level object

## Decision

**Widen the re-type lattice on ingested traces.** Keep the mechanism (L0, Wilson, ABSTAIN, no auto-apply). Add role actions and a report-level orchestrator block. Advisor fields only (`advisor.orchestrator.*`). Never invent `gen_ai.orchestrator.*`.

Capability name in docs: Architecture Advisor. Package name stays `superdeterminism`. `FlipToDet` remains the JSON value for collapse-to-tool.

## Rationale

Matches “improve the agentic architecture” without colliding with searchers or linters. The hub is the control-flow owner; scoring leaves in isolation misses unbounded supervisors.

## Consequences

- Path-shape (`p_path`) and next-hop (`p_next`) join output `p_mode`.
- Existing FlipToDet fixtures must still fire when output is mode-stable (lower rung than FlipToWorkflow).
- Ambiguous hub → orchestrator ABSTAIN; leaf flips still run.
- Doctrine: [agent-architectures.md](../agent-architectures.md), [type-lattice.md](../type-lattice.md), [orchestrator.md](../orchestrator.md).
