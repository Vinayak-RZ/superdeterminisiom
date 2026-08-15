# Overview

**Superdeterminism** / **Determinism Advisor** is a design-time advisor for existing agentic architectures.

It will take production traces, reconstruct the graph, and estimate what would happen if a step flipped from stochastic (LLM / subagent) to deterministic (tool / function), or the reverse — then recommend a refactor with evidence.

> Counterfactual *re-typing* of nodes between deterministic tools and stochastic LLM/subagents, on ingested production graphs.

This document is the product brief. Methodology lives in [methodology.md](methodology.md). Adjacent tools live in [landscape.md](landscape.md).

## The problem

Every team on LangChain, LangGraph, CrewAI, or a custom stack eventually asks: *should this step be a typed tool call, or should I hand it to the model?*

Today that decision is intuition, then (maybe) validated after the fact. Eval platforms score what a trace **did**. They do not simulate what it **would do** under a different determinism split, and they do not recommend a structural change.

The failure modes are symmetric:

- Over-delegate to LLMs where a function would be cheaper, faster, and auditable.
- Over-constrain with rigid tools where the task needs judgment, and the agent breaks on the first uncoded edge case.

In regulated or cost-sensitive systems, non-determinism has to be justified (audit) or minimized (tokens, latency). There is no tooling that closes that loop with evidence.

## What it does

1. **Ingest** — read existing execution traces over OTLP / GenAI semantic conventions. No new instrumentation if you already emit LangSmith, Langfuse, MLflow, or raw OTel. See [ingestion.md](ingestion.md).
2. **Map** — reconstruct the architecture as a graph. Tag each step as currently deterministic or non-deterministic from observed behavior. See [architecture.md](architecture.md).
3. **Simulate** — for ambiguous or high-variance steps, estimate the counterfactual. v0 is offline (historical variance + tape splice). It does not re-run the production LLM by default. See [methodology.md](methodology.md).
4. **Recommend** — a ranked list of flips with estimated deltas (cost, latency, failure, variance, auditability, compliance) and confidence intervals. Abstain when the evidence is weak.
5. **Assist the refactor** — for LangGraph/LangChain, emit a report and an optional scaffold. v0 does **not** rewrite the graph or open a PR. See [refactor.md](refactor.md).

## Who it is for

Developers and teams operating production agentic systems who are past the prototype stage and need to decide, with evidence, where determinism belongs — especially where non-determinism must be justified or minimized.

## Why now

- OTel / GenAI semantic conventions matured enough in 2026 that traces are portable across LangSmith, Langfuse, and MLflow. A simulator can plug into existing telemetry instead of requiring new instrumentation. The spec is still **Development**; we pin a commit. See [ingestion.md](ingestion.md).
- Existing evaluation tooling observes and scores runs. Counterfactual replay tools intervene on actions or agents. Architecture-search papers invent new workflows offline. None flip *determinism class* on an ingested production graph and recommend a refactor. See [landscape.md](landscape.md).

## v0 scope

- LangGraph / LangChain 1.x only (`create_agent`, not deprecated `create_react_agent`)
- Read-only OTLP ingest
- Recommendation as a report (which steps, why, estimated delta) before any scaffold
- No live agent control, no auto-apply

Details: [roadmap.md](roadmap.md), [adapters.md](adapters.md).

## Status

This repository is the research contract. There is no simulator code yet. Product implementation needs a separate approved project-mode plan.
