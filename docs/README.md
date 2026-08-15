# Superdeterminism documentation

Project: **Superdeterminism**. Capability: **Determinism Advisor**.

Execution contract: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md). Status: [PROGRESS.md](../PROGRESS.md). Overview: [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md).

Positioning sentence:

> Counterfactual *re-typing* of nodes between deterministic tools and stochastic LLM/subagents, on ingested production graphs.

Read in this order if you are new:

1. [overview.md](overview.md) — what the product is and is not
2. [landscape.md](landscape.md) — adjacent tools and claim hygiene
3. [ingestion.md](ingestion.md) — how traces enter
4. [architecture.md](architecture.md) — the domain graph
5. [methodology.md](methodology.md) — how a flip is estimated
6. [adapters.md](adapters.md) and [refactor.md](refactor.md) — LangGraph v0 surface
7. [roadmap.md](roadmap.md) — P0 / P1 / P2 index
8. [p1-langgraph.md](p1-langgraph.md) — P1 spec (implemented)
9. [p2-ecosystem.md](p2-ecosystem.md) — P2 spec (not built)
10. [usage.md](usage.md) — P0 CLI
11. [references.md](references.md) — sources (dated 2026-08-15)

## Research docs

| Doc | What it covers |
|---|---|
| [overview.md](overview.md) | Problem, loop, audience, why now |
| [landscape.md](landscape.md) | Adjacent tools; safe vs unsafe claims |
| [ingestion.md](ingestion.md) | OTel GenAI substrate |
| [architecture.md](architecture.md) | `node_kind`, `det.class` |
| [methodology.md](methodology.md) | How a flip is estimated |
| [adapters.md](adapters.md) | LangGraph v0 |
| [refactor.md](refactor.md) | Report + scaffold; no auto-apply |
| [roadmap.md](roadmap.md) | P0 / P1 / P2 index |
| [p1-langgraph.md](p1-langgraph.md) | LangGraph adapter spec |
| [p2-ecosystem.md](p2-ecosystem.md) | Lang ecosystem + other stacks spec |
| [usage.md](usage.md) | P0 CLI for agents and humans |
| [references.md](references.md) | Bibliography |

## Architecture decisions

| ADR | Decision |
|---|---|
| [0001-otel-ingest.md](decisions/0001-otel-ingest.md) | Ingest OTLP; keep Advisor fields out of `gen_ai.*` |
| [0002-v0-offline-first.md](decisions/0002-v0-offline-first.md) | Offline L0 / historical estimators before live L2 replay |
| [0003-no-auto-apply.md](decisions/0003-no-auto-apply.md) | Report + optional scaffold; never auto-apply |
| [0004-agnostic-core.md](decisions/0004-agnostic-core.md) | Core has zero framework deps; adapters later |

Index: [DECISIONS.md](../DECISIONS.md).

## Cursor coding-config guides

Vendored from [cursor-config-coding](https://github.com/Vinayak-RZ/cursor-config-coding). Not Superdeterminism product docs.

| Doc | What it covers |
|---|---|
| [LEARNING_AND_RESEARCH.md](cursor-config/LEARNING_AND_RESEARCH.md) | Learn-while-building workflow |
| [SPEC_KIT.md](cursor-config/SPEC_KIT.md) | Spec-driven development |
| [TECH_STACK_SKILLS.md](cursor-config/TECH_STACK_SKILLS.md) | Optional stack skills |
| [MCP_SETUP.md](cursor-config/MCP_SETUP.md) | Agent Patterns Catalog MCP |
| [INDUSTRY_PRACTICES.md](cursor-config/INDUSTRY_PRACTICES.md) | Industry practices the rules encode |
