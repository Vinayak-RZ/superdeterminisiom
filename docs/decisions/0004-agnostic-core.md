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

- P0 cannot use `langgraph_node` until P1 (generic ops only).
- Optional extras must not leak into core tests.
