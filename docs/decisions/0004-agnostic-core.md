# ADR 0004 — Agnostic core, framework adapters later

- **Status:** accepted
- **Date:** 2026-08-15
- **Index:** [DECISIONS.md](../../DECISIONS.md)

## Context

Users need this on LangGraph **and** on other agent stacks. Putting LangChain in the core would lock the architecture and block a “raw” custom agent.

## Alternatives

- LangGraph-only package
- Monolith that if-imports every framework
- Core with zero framework deps; extras for adapters

## Decision

**P0 = agnostic core.** P1 = LangGraph/LangChain extra. P2 = Lang ecosystem sinks + CrewAI/MAF/custom adapters. Core never imports those libraries.

## Rationale

One ingest/map/recommend loop. Adapters only translate. Agents and humans call the same CLI.

## Consequences

- P0 may *read* `langgraph_node` as a generic attribute. P1 owns Lang quirks (checkpoint ns, triggers, retriever→embeddings) and the scaffold. See [p1-langgraph.md](../p1-langgraph.md).
- P2 owns the `Protocol` + registry once a second adapter exists. See [p2-ecosystem.md](../p2-ecosystem.md).
- Optional extras must not leak into core tests.
