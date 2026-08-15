# Superdeterminism

**Determinism Advisor** — a design-time advisor for agentic architectures.

> **What it is:** A research contract (and, later, a tool) that estimates which steps in an existing agent graph should be deterministic tools versus stochastic LLM/subagents.
> **What it is not:** A runtime eval platform, a workflow searcher, or a LangChain-only plugin.
> **Primary interface today:** `python -m superdeterminism recommend` (JSON in/out) plus the research docs.

The GitHub repository is still named `superdeterminisiom`. The project name is **Superdeterminism**.

## TL;DR

- Problem: teams guess whether a step should be a typed tool or an LLM/subagent.
- Eval tools score the path you already ran. Architecture-search papers invent new graphs offline. Neither flips *determinism class* on an ingested production graph.
- v0 (not built): ingest OTLP → map the graph → offline counterfactual → recommend or abstain → optional LangGraph scaffold. No auto-apply.
- **P0 core is agnostic** (no LangChain import). P1 is LangGraph. P2 is the rest of the Lang ecosystem and other agent stacks.
- Cursor rules/skills are vendored from [cursor-config-coding](https://github.com/Vinayak-RZ/cursor-config-coding).

## Table of contents

1. [Vision](#1-vision)
2. [Architecture](#2-architecture)
3. [Quickstart](#3-quickstart)
4. [Project structure](#4-project-structure)
5. [Documentation](#5-documentation)
6. [Cursor coding config](#6-cursor-coding-config)
7. [Roadmap](#7-roadmap)
8. [Glossary](#8-glossary)
9. [License](#9-license)

Omitted until they exist: HTTP API, deployment. CLI: [docs/usage.md](docs/usage.md). Tests: `python -m pytest -q`.

## 1. Vision

### What it is

An open-source advisor that will take production agent traces, reconstruct the architecture, and estimate counterfactual **re-typing** of nodes between deterministic tools and stochastic LLM/subagents — with evidence, not gut feel.

### What it is not

- Not “score the path you already ran” (LangSmith, MLflow, DeepEval, Galileo, Langfuse).
- Not “search a new workflow from scratch” (MaAS, AFlow).
- Not a claim that nobody does counterfactual agent simulation (CAR, CausalFlow, Tracefork, AgentReplay, and counterfact already do). The unclaimed layer is the **determinism-class flip + refactor recommendation**. See [docs/landscape.md](docs/landscape.md).

### Who it is for

Developers past prototype, especially in regulated or cost-sensitive systems.

### Success criteria (docs phase)

A later agent can implement v0 without inventing whitespace claims, ingest mappings, or flip methodology.

## 2. Architecture

Documented target, not implemented. Detail: [docs/architecture.md](docs/architecture.md).

```text
OTLP traces → normalize spans → architecture graph (node_kind, det.class)
  → L0 offline counterfactual → recommend or ABSTAIN → report + optional scaffold
```

Advisor-owned fields live in `advisor.*` / `det.*`. Never invent `gen_ai.*` keys.

## 3. Quickstart

```bash
pip install -e ".[dev]"
python -m superdeterminism recommend tests/fixtures/advisor_stable_llm.json --n-min 1 --stdout json
python -m pytest -q
```

Agents: always `--stdout json`. Humans can add `--md report.md`. Details: [docs/usage.md](docs/usage.md).

Read [docs/overview.md](docs/overview.md) and [docs/methodology.md](docs/methodology.md) before changing decision rules.

## 4. Project structure

```text
AGENTS.md                 Agent instructions + claim hygiene
PROJECT_OVERVIEW.md       Purpose, architecture, constraints
IMPLEMENTATION_PLAN.md    Nawab execution contract
PROGRESS.md               Live phase status
DECISIONS.md              Decision index
LEARNING.md               Phase learnings
LICENSE                   Apache-2.0
pyproject.toml            P0 package (stdlib only)
src/superdeterminism/     Agnostic core
tests/                    Fixtures + pytest
.cursor/                  Vendored coding config (rules, skills, MCP)
docs/                     Research contract + ADRs
docs/cursor-config/       Vendored cursor-config-coding guides
docs/decisions/           ADRs 0001–0003
scripts/                  Vendor PowerShell helpers
```

## 5. Documentation

| Doc | What it covers |
|---|---|
| [docs/README.md](docs/README.md) | Doc map |
| [docs/overview.md](docs/overview.md) | Problem, loop, audience, why now |
| [docs/landscape.md](docs/landscape.md) | Adjacent tools; safe vs unsafe claims |
| [docs/ingestion.md](docs/ingestion.md) | OTel GenAI substrate |
| [docs/architecture.md](docs/architecture.md) | `node_kind`, `det.class` |
| [docs/methodology.md](docs/methodology.md) | How a flip is estimated |
| [docs/adapters.md](docs/adapters.md) | LangGraph v0 |
| [docs/refactor.md](docs/refactor.md) | Report + scaffold; no auto-apply |
| [docs/roadmap.md](docs/roadmap.md) | P0 / P1 / P2 |
| [docs/usage.md](docs/usage.md) | CLI for agents and humans |
| [docs/references.md](docs/references.md) | Bibliography (dated 2026-08-15) |
| [docs/decisions/](docs/decisions/) | ADRs 0001–0003 |
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | Purpose, constraints |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Nawab plan |
| [DECISIONS.md](DECISIONS.md) | Decision index |
| [LEARNING.md](LEARNING.md) | Phase learnings |

## 6. Cursor coding config

Vendored from [cursor-config-coding](https://github.com/Vinayak-RZ/cursor-config-coding)@437a548. Pin: [`.cursor/VENDOR.md`](.cursor/VENDOR.md). Guides: [docs/cursor-config/](docs/cursor-config/).

## 7. Roadmap

See [docs/roadmap.md](docs/roadmap.md). Product code needs a separate approved project-mode plan.

## 8. Glossary

| Term | Meaning |
|---|---|
| Determinism class / `det.class` | Whether a node is a function, an LLM, a composite, etc. Advisor-owned. |
| Flip | Counterfactual re-typing of a node (FlipToDet / FlipToNondet). |
| L0 / L1 / L2 | Tape splice / hybrid fork / live policy swap. v0 default is L0. |
| ABSTAIN | First-class recommendation: evidence too weak. |
| STRENGTHEN_SDB | Keep the proposer; harden the deterministic gate. |
| `node_kind` | Internal enum: tool, reasoner, subagent, router, retriever, workflow. |

## 9. License

Apache License 2.0. See [LICENSE](LICENSE).
