# Overview

**Superdeterminism** / **Architecture Advisor** is a design-time advisor for existing agentic architectures.

It takes production traces, reconstructs the graph (including who owns control flow), and estimates what would happen if a step — or the orchestrator — flipped architectural *role*: predefined workflow vs subagent vs tool vs router vs LLM — then recommends a refactor with evidence.

> Counterfactual *re-typing* of nodes — and of the orchestrator that owns control flow — on ingested production graphs.

This document is the product brief. Doctrine: [agent-architectures.md](agent-architectures.md). Lattice: [type-lattice.md](type-lattice.md). Hub: [orchestrator.md](orchestrator.md). Adjacent tools: [landscape.md](landscape.md).

Determinism class (`det.class`) is one *axis* of the lattice, not the whole product. The package name stays `superdeterminism`.

## The problem

Every team on LangChain, LangGraph, CrewAI, or a custom stack eventually asks more than *tool vs LLM*:

- Should this envelope be a **predefined workflow** or an open agent loop?
- Should this hop be a **sub-agent** (isolated context) or stay in the parent?
- Should next-hop be a **code router** or a model choice?
- Is the **orchestrator** unbounded, over-orchestrating, or reaching a refund with no gate?

Today those decisions are intuition. Eval platforms score what a trace **did**. Architecture-search papers invent new graphs offline. Neither re-types roles on an ingested production graph.

Failure modes are symmetric and now wider than over/under-using tools:

- Over-delegate to LLMs or supervisors where a function or DAG would be cheaper and auditable.
- Over-constrain with rigid tools or a supervisor-of-one where the task needs judgment or a single agent + tools.

## What it does

1. **Ingest** — OTLP / GenAI semantic conventions. See [ingestion.md](ingestion.md).
2. **Map** — reconstruct the architecture graph. Tag `node_kind`, `det.class`, and the orchestrator envelope. See [architecture.md](architecture.md).
3. **Simulate** — offline L0 (historical variance + path shape). No production-LLM re-run by default. See [methodology.md](methodology.md).
4. **Recommend** — role flips, orchestrator bound/strengthen/collapse/code-route, or **ABSTAIN**, with CIs.
5. **Assist** — report + optional write-only scaffold. Never rewrite the graph. See [refactor.md](refactor.md).

## Who it is for

Developers and coding agents past prototype who need evidence for where control flow and determinism belong — especially in regulated or cost-sensitive systems.

## Why now

- OTel / GenAI conventions are portable enough (still **Development**; we pin a commit).
- Eval tools observe. Replay tools intervene on the *same* types. Search papers invent graphs. None flip *role* (including the hub) on an ingested graph. See [landscape.md](landscape.md).

## v0 scope

- Agnostic core + optional adapters (LangGraph, Langfuse, MAF, CrewAI, custom)
- Read-only ingest
- Report before any scaffold
- No live agent control, no auto-apply

## Status

P0–P2 are implemented (core, LangGraph adapter, ecosystem). P3 expands the recommender from tool-vs-LLM to the role lattice and a first-class orchestrator block. CLI: [usage.md](usage.md).
