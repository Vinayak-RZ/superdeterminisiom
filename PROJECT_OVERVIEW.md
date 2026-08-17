# Project overview

## Purpose

**Superdeterminism** (capability: **Architecture Advisor**) is an open-source design-time advisor for agentic architectures. It ingests production traces, reconstructs the agent graph (including the control-flow owner), estimates counterfactual **role** flips (workflow ↔ subagent ↔ tool ↔ router ↔ LLM, plus orchestrator actions), and recommends a refactor with evidence.

The GitHub repository name remains `superdeterminisiom`. Determinism class is one axis of the lattice, not the whole product.

## System overview

P0 is an **agnostic Python core** (`src/superdeterminism/`) with a CLI. It does not import LangChain. P1 is LangGraph. P2 is other stacks. P3 widens the recommender from tool-vs-LLM to the role lattice and a graph-level orchestrator. P4 adds L0 path census and tape-splice counterfactuals.

The product loop:

1. **Ingest** OTLP / GenAI semantic convention traces.
2. **Map** spans to `node_kind`, `det.class`, and the orchestrator envelope.
3. **Simulate** offline (v0): historical variance + path shape. No production-LLM re-run by default.
4. **Recommend** role flips, orchestrator bound/strengthen/collapse/code-route, or ABSTAIN.
5. **Assist** via a report and optional scaffold. Never auto-apply.

## High-level architecture

```text
OTLP traces → normalize → architecture graph + orchestrator
  → L0 counterfactual (p_mode, p_path, p_next)
  → ranked recommendations or ABSTAIN → report + optional scaffold
```

Differentiation: counterfactual *re-typing* of nodes — and of the orchestrator — on ingested production graphs. Not scoring the path you already ran. Not searching a new workflow from scratch.

## Constraints

- Do not claim “nobody does counterfactual agent simulation,” “nobody advises workflow vs agent,” or “nobody does orchestration.”
- OpenTelemetry GenAI conventions are **Development**; pin a commit, not a tag.
- Advisor fields: `advisor.*` / `det.*`. Never invent `gen_ai.*` (including `gen_ai.orchestrator.*`).
- Temperature 0 is not a seed. Simulation ≠ production.
- Commit / spend / PII / auth nodes stay deterministic gates. Ungated hub → `StrengthenOrchestrator`.
- Core never imports LangChain / LangGraph / CrewAI / MAF. Adapters only translate.
- No auto-apply. License: Apache-2.0.
