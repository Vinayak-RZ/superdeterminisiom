# ADR 0001 — Ingest OTLP; keep Advisor fields out of `gen_ai.*`

- **Status:** accepted
- **Date:** 2026-08-15
- **Index:** [DECISIONS.md](../../DECISIONS.md) D4

## Context

We need traces from LangSmith, Langfuse, MLflow, and raw OTel without a new instrumentation SDK. OpenTelemetry GenAI conventions are **Development**, moved out of core in v1.42.0, and have no tagged release in `semantic-conventions-genai`.

## Alternatives

- A Superdeterminism-specific tracer SDK
- Vendor-native APIs only (LangSmith run tree, MLflow traces)
- Invent `gen_ai.determinism.*` keys

## Decision

Ingest OTLP. Normalize SIG + LangSmith + OpenInference + legacy dual keys. Persist Advisor fields in `advisor.*` / `det.*` only. Pin a GenAI commit in [ingestion.md](../ingestion.md).

## Rationale

A new SDK would block adoption. Vendor-native APIs would lock v0 to one sink. Inventing `gen_ai.*` keys will collide when the spec moves.

## Consequences

- Mapping tables must be versioned (`advisor.schema_version`).
- LangSmith’s retriever→embeddings bug and Azure’s every-node-is-`invoke_agent` must be handled in code later.
- Spec drift is a standing maintenance cost.
