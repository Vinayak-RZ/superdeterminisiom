# Superdeterminism documentation

Project: **Superdeterminism**. Capability: **Determinism Advisor**.

Read in this order if you are new:

1. [overview.md](overview.md) — what the product is and is not
2. [landscape.md](landscape.md) — adjacent tools and claim hygiene
3. [ingestion.md](ingestion.md) — how traces enter
4. [architecture.md](architecture.md) — the domain graph
5. [methodology.md](methodology.md) — how a flip is estimated
6. [adapters.md](adapters.md) and [refactor.md](refactor.md) — LangGraph v0 surface
7. [roadmap.md](roadmap.md) — what ships when
8. [references.md](references.md) — sources (dated 2026-08-15)

Architecture decisions:

| ADR | Decision |
|---|---|
| [0001-otel-ingest.md](decisions/0001-otel-ingest.md) | Ingest OTLP; keep Advisor fields out of `gen_ai.*` |
| [0002-v0-offline-first.md](decisions/0002-v0-offline-first.md) | Offline L0 / historical estimators before live L2 replay |
| [0003-no-auto-apply.md](decisions/0003-no-auto-apply.md) | Report + optional scaffold; never auto-apply |

Positioning sentence used everywhere:

> Counterfactual *re-typing* of nodes between deterministic tools and stochastic LLM/subagents, on ingested production graphs.

Cursor coding-config guides (vendored from [cursor-config-coding](https://github.com/Vinayak-RZ/cursor-config-coding)):

| Doc | What it covers |
|---|---|
| [LEARNING_AND_RESEARCH.md](LEARNING_AND_RESEARCH.md) | Learn-while-building workflow |
| [SPEC_KIT.md](SPEC_KIT.md) | Spec-driven development |
| [TECH_STACK_SKILLS.md](TECH_STACK_SKILLS.md) | Optional stack skills |
| [MCP_SETUP.md](MCP_SETUP.md) | Agent Patterns Catalog MCP |
| [INDUSTRY_PRACTICES.md](INDUSTRY_PRACTICES.md) | Industry practices the rules encode |
