# Project overview

## Purpose

**Superdeterminism** (capability: **Determinism Advisor**) is an open-source design-time advisor for agentic architectures. It will ingest production traces, reconstruct the agent graph, estimate counterfactual determinism-class flips (tool ↔ LLM/subagent), and recommend a refactor with evidence.

The GitHub repository name remains `superdeterminisiom`.

## System overview

P0 ships an **agnostic Python core** (`src/superdeterminism/`) with a CLI. It does not import LangChain. LangGraph is P1 ([docs/p1-langgraph.md](docs/p1-langgraph.md)); other stacks and the rest of the Lang ecosystem are P2 ([docs/p2-ecosystem.md](docs/p2-ecosystem.md)).

The intended product loop:

1. **Ingest** OTLP / GenAI semantic convention traces (LangSmith, Langfuse, MLflow, or raw OTel).
2. **Map** spans to `node_kind` and `det.class`.
3. **Simulate** offline (v0): historical variance + tape splice. No production-LLM re-run by default.
4. **Recommend** FlipToDet, FlipToNondet, STRENGTHEN_SDB, or ABSTAIN, with estimated deltas and confidence intervals.
5. **Assist** LangGraph/LangChain via a report and optional scaffold. Never auto-apply.

## High-level architecture

```text
OTLP traces → normalize → architecture graph → L0 counterfactual
  → ranked recommendations or ABSTAIN → report + optional scaffold
```

Differentiation: counterfactual *re-typing* of nodes on ingested production graphs — not scoring the path you already ran, and not searching a new workflow from scratch.

## Constraints

- Do not claim “nobody does counterfactual agent simulation.”
- OpenTelemetry GenAI conventions are **Development**; pin a commit, not a tag.
- Advisor fields: `advisor.*` / `det.*`. Never invent `gen_ai.*`.
- Temperature 0 is not a seed. Simulation ≠ production.
- Commit / spend / PII / auth nodes stay deterministic gates regardless of accuracy.
- Core never imports LangChain / LangGraph / CrewAI / MAF. Adapters only translate.
- P1 adapter: LangGraph/LangChain 1.x `create_agent` (not `create_react_agent`) + custom `StateGraph`. Implemented.
- P2: Lang sinks + CrewAI / MAF / custom via one adapter contract. Implemented.
- No auto-apply. License: Apache-2.0.
