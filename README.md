# Superdeterminism

**Determinism Advisor** — a design-time advisor for agentic architectures.

> **What it is:** A research contract (and, later, a tool) that estimates which steps in an existing agent graph should be deterministic tools versus stochastic LLM/subagents.
> **What it is not:** A runtime eval platform, a workflow searcher, or a shipping simulator. There is no application code in this repository yet.
> **Primary interface today:** Markdown research docs and Cursor agent config.

The GitHub repository is still named `superdeterminisiom`. The project name is **Superdeterminism**.

## TL;DR

- Problem: teams guess whether a step should be a typed tool or an LLM/subagent.
- Eval tools score the path you already ran. Architecture-search papers invent new graphs offline. Neither flips *determinism class* on an ingested production graph.
- v0 (not built): ingest OTLP → map the graph → offline counterfactual → recommend or abstain → optional LangGraph scaffold. No auto-apply.
- This repo is **docs-first**. Research files land in Phase A of the approved plan.
- Cursor rules/skills are vendored from [cursor-config-coding](https://github.com/Vinayak-RZ/cursor-config-coding).

## Table of contents

1. [Vision](#1-vision)
2. [Architecture](#2-architecture)
3. [Quickstart](#3-quickstart)
4. [Project structure](#4-project-structure)
5. [Documentation that exists](#5-documentation-that-exists)
6. [Cursor coding config](#6-cursor-coding-config)
7. [License](#7-license)

## 1. Vision

### What it is

An open-source advisor that will take production agent traces, reconstruct the architecture, and estimate counterfactual **re-typing** of nodes between deterministic tools and stochastic LLM/subagents — with evidence, not gut feel.

### What it is not

- Not “score the path you already ran” (LangSmith, MLflow, DeepEval, Galileo, Langfuse).
- Not “search a new workflow from scratch” (MaAS, AFlow).
- Not a claim that nobody does counterfactual agent simulation (CAR, CausalFlow, Tracefork, AgentReplay, and counterfact already do). The unclaimed layer is the **determinism-class flip + refactor recommendation**.

### Who it is for

Developers past prototype, especially in regulated or cost-sensitive systems.

### Success criteria (docs phase)

A later agent can implement v0 without inventing whitespace claims, ingest mappings, or flip methodology.

## 2. Architecture

Documented target, not implemented:

```text
OTLP traces → normalize spans → architecture graph (node_kind, det.class)
  → L0 offline counterfactual → recommend or ABSTAIN → report + optional scaffold
```

Advisor-owned fields live in `advisor.*` / `det.*`. Never invent `gen_ai.*` keys.

## 3. Quickstart

There is nothing to install or run. Clone the repo and read:

1. [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
2. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
3. [AGENTS.md](AGENTS.md)

Research docs (`docs/overview.md` and siblings) are **not written yet**. They are Phase A of the plan. Do not add links to them until they exist.

## 4. Project structure

```text
AGENTS.md                 Agent instructions + claim hygiene
PROJECT_OVERVIEW.md       Purpose, architecture, constraints
IMPLEMENTATION_PLAN.md    Nawab execution contract
PROGRESS.md               Live phase status
DECISIONS.md              Decision index
LEARNING.md               Phase learnings
LICENSE                   Apache-2.0
.cursor/                  Vendored coding config (rules, skills, MCP)
docs/README.md            Doc map (only files that exist)
docs/cursor-config/       Vendored cursor-config-coding guides
scripts/                  Vendor PowerShell helpers
```

## 5. Documentation that exists

| Doc | What it covers |
|---|---|
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | Purpose, architecture, constraints |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Nawab plan (18 sections) |
| [PROGRESS.md](PROGRESS.md) | Phase status |
| [DECISIONS.md](DECISIONS.md) | Decision index |
| [LEARNING.md](LEARNING.md) | What we learned per phase |
| [AGENTS.md](AGENTS.md) | Agent workflow + claim hygiene |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [docs/README.md](docs/README.md) | Doc map |
| [docs/cursor-config/](docs/cursor-config/) | Vendored coding-config guides |

Planned research docs (Phase A): overview, landscape, ingestion, architecture, methodology, adapters, refactor, roadmap, references, ADRs. Listed here as names only until the files exist.

## 6. Cursor coding config

Vendored from [cursor-config-coding](https://github.com/Vinayak-RZ/cursor-config-coding)@437a548. Pin: [`.cursor/VENDOR.md`](.cursor/VENDOR.md).

- [`.cursor/rules/`](.cursor/rules/) — 21 project rules
- [`.cursor/skills/`](.cursor/skills/) — ponytail, nawab-plans, spec-kit, architecture skills
- [`.cursor/mcp.json`](.cursor/mcp.json) — Agent Patterns Catalog
- [`.cursor/environment.json`](.cursor/environment.json) — Cloud Agent presence check

## 7. License

Apache License 2.0. See [LICENSE](LICENSE).
