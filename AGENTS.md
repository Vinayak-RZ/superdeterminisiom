# Superdeterminism — Agent instructions

This repository vendors [cursor-config-coding](https://github.com/Vinayak-RZ/cursor-config-coding) at `.cursor/` (rules, skills, MCP). Pin: see [`.cursor/VENDOR.md`](.cursor/VENDOR.md).

Project name: **Superdeterminism**. Capability: **Architecture Advisor**.
GitHub repo name remains `superdeterminisiom`.

## What this repo is

An open-source **design-time advisor** for agentic architectures. It ingests production traces (OTLP / GenAI semconv), reconstructs the agent graph (including who owns control flow), estimates counterfactual **role** flips (workflow ↔ subagent ↔ tool ↔ router ↔ LLM, plus orchestrator bound/collapse/code-route), and recommends a refactor with evidence.

Differentiation (do not weaken this):

> Counterfactual *re-typing* of nodes — and of the orchestrator that owns control flow — on ingested production graphs — not “score the path you already ran,” and not “search a new workflow from scratch.”

## Current status

**P0–P4 are implemented** (P4 = L0 path census + tape-splice counterfactuals). Core has no LangChain import. Adapters live under `src/superdeterminism/adapters/`.

```bash
python -m superdeterminism recommend traces.json --stdout json
python -m superdeterminism recommend traces.json --adapter langgraph --stdout json
python -m superdeterminism recommend traces.json --adapter custom --stdout json
python -m superdeterminism recommend --traces-dir DIR --stdout json
python -m superdeterminism scaffold report.json --out scaffold/RUN
python -m superdeterminism simulate traces.json --stdout json
```

Specs: [docs/p1-langgraph.md](docs/p1-langgraph.md), [docs/p2-ecosystem.md](docs/p2-ecosystem.md). Usage: [docs/usage.md](docs/usage.md). Do not add framework extras to core. Do not auto-apply refactors. Do not call a model without `--opt-in-l1`.

Read before any product work:

1. [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
2. [docs/overview.md](docs/overview.md)
3. [docs/landscape.md](docs/landscape.md) — claim hygiene
4. [docs/methodology.md](docs/methodology.md)
5. [docs/agent-architectures.md](docs/agent-architectures.md) / [docs/type-lattice.md](docs/type-lattice.md) / [docs/orchestrator.md](docs/orchestrator.md)
6. [docs/decisions/](docs/decisions/)
7. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)

## Claim hygiene

- Do **not** say “nobody does counterfactual agent simulation.”
- Do **not** say “nobody advises workflow vs agent” or “nobody does orchestration.”
- Do say “nobody re-types architectural roles (including the orchestrator) on an ingested production graph and recommends a refactor.”
- Mark OpenTelemetry GenAI conventions as **Development**. Pin a commit, not a tag.
- Advisor-owned fields live in `advisor.*` / `det.*`. Never invent `gen_ai.*` keys (including `gen_ai.orchestrator.*`).
- Temperature 0 is not a seed. Do not promise bit-exact architecture advice from a single replay.
- Simulation ≠ production. A canary with the same outcome vector is confirmatory.

## Scope

- **P0 (now):** agnostic core — OTLP/flat ingest, L0 recommend, JSON/MD report
- **P1 (now):** LangGraph / LangChain adapter — [docs/p1-langgraph.md](docs/p1-langgraph.md)
- **P2 (now):** Langfuse / custom / CrewAI / MAF + batch + L1 gate — [docs/p2-ecosystem.md](docs/p2-ecosystem.md)
- **P3 (now):** role lattice + first-class orchestrator — [docs/type-lattice.md](docs/type-lattice.md), [docs/orchestrator.md](docs/orchestrator.md)
- **P4 (now):** L0 path census + tape-splice counterfactuals — [docs/simulation.md](docs/simulation.md)
- No auto-apply, no in-place `graph.py` rewrite, no live production-LLM re-runs by default

---

# Coding — Agent Mode

Engineering workflow: **ponytail → nawab-plans (Plan mode) → (spec-kit for features) → research → plan → approve → implement → validate → commit → learn**.

## Ponytail — mandatory gate for all coding

**Before writing or modifying any code**, read and apply the `ponytail` skill (`.cursor/skills/ponytail/SKILL.md`). Always-on rule: `ponytail.mdc`.

From [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) — lazy senior dev ladder for minimal, production-grade diffs. **Skills + MDC only** (no Ponytail MCP).

| Layer | What | When |
|-------|------|------|
| Rule | `ponytail.mdc` | Always on — requires reading the `ponytail` skill before code |
| Skill | `ponytail` | **Read first** on every coding task (write, fix, refactor, add deps) |
| Review | `ponytail-review`, `ponytail-audit` | After implementation or on request — hunt over-engineering |

Climb the ladder after you understand the problem: YAGNI → reuse codebase → stdlib → native → installed dep → one line → minimum that works. Never cut validation, security, accessibility, or error handling that prevents data loss.

Intensity: `full` (default). User can say `/ponytail ultra` for stricter YAGNI or `stop ponytail` to disable.

## Nawab Plans — mandatory in Plan mode

**Whenever in Plan mode or drafting an implementation plan**, read and apply `nawab-plans` (`.cursor/skills/nawab-plans/SKILL.md`). Enforced by `planning.mdc`.

| Asset | Role |
|-------|------|
| `nawab-plans` skill | Master execution plan structure (18 sections) |
| `PLAN.template.md` | Copy into `IMPLEMENTATION_PLAN.md` |
| `SUBAGENT_ORCHESTRATION.md` | Spawn map / lead vs subagent roles |

Do not invent a thinner plan format. Collapse unused sections as `N/A` — do not skip the skill.

## Spec Kit — Spec-Driven Development (features / greenfield)

From [github/spec-kit](https://github.com/github/spec-kit). Pre-installed skills: `speckit-*`. Rule: `speckit.mdc`. Guide: [docs/cursor-config/SPEC_KIT.md](docs/cursor-config/SPEC_KIT.md).

Use for **new features / greenfield**, not one-line fixes. Target repo needs `.specify/`.

Order: `constitution` → `specify` → (`clarify`) → `plan` → (`checklist`) → `tasks` → (`analyze`) → `implement` → (`converge`).

During implement, still apply **ponytail** on every code change.

## Before any task

1. Read this file and all `.cursor/rules/` (start with `rule-awareness`, `ponytail`, `planning`, `core-engineering`, `learn-and-research`).
2. **Coding tasks:** read `ponytail` skill and climb the ladder before proposing or writing code.
3. **Plan mode / any implementation plan:** read `nawab-plans` skill **compulsorily** and follow `PLAN.template.md`.
4. **Feature / greenfield:** follow `speckit.mdc` and Spec Kit skills when the user wants specs-first or the change is multi-phase; structure delivery with `nawab-plans`.
5. Follow `planning.mdc` — analyze, plan, **get user approval** before non-trivial coding.
6. Follow `communication.mdc` — surface risks and tradeoffs explicitly.
7. Unfamiliar tech → research brief for the user before architectural choices.

## Architecture (when designing or refactoring)

| Domain | Skill | Rule |
|--------|-------|------|
| Frontend / UI / Next.js | `frontend-architecture` | `frontend-architecture.mdc` |
| Backend / API / data | `backend-architecture` | `backend-architecture.mdc` |
| AI agents / LLM / tools | `agentic-system-design` | `agentic-systems.mdc` |
| Any major trade-off | `system-design-tradeoffs` | `trade-offs.mdc` |

Before large refactors, consider `graphify` on the affected directory.

## Learning & documentation

| Need | Skill / doc |
|------|-------------|
| Learn while building | `learn-while-building` |
| Exhaustive README | `extensive-readme` |
| Workflow guide | [docs/cursor-config/LEARNING_AND_RESEARCH.md](docs/cursor-config/LEARNING_AND_RESEARCH.md) |

End each phase with a short **What you learned** summary in [LEARNING.md](LEARNING.md).

## Git commits and pushes

After each validated phase or meaningful feature:

- **Conventional commit** per `git-commit-discipline.mdc`
- **Push check** after every commit — auto-push when **≥ 10 unpushed** commits, or when user asks

## MCP (live architecture patterns)

Default server: **agent-patterns** → [Agent Patterns Catalog](https://www.agentpatternscatalog.org/)
Config: `.cursor/mcp.json` | Guide: [docs/cursor-config/MCP_SETUP.md](docs/cursor-config/MCP_SETUP.md)

For agentic design, **query MCP first** (`find_pattern`, `recommend_recipe`, `pattern_for_symptom`) then apply `agentic-system-design` + `system-design-tradeoffs`.

Minimal-code discipline is **not** via MCP — use `ponytail.mdc` + the `ponytail` skill.

Reload Cursor after changing `mcp.json`.

## During implementation

7. Apply `execution.mdc` — phase-based work only; minimal scope; **read `ponytail` skill** on every edit.
8. Stack-specific optional skills: [docs/cursor-config/TECH_STACK_SKILLS.md](docs/cursor-config/TECH_STACK_SKILLS.md).
9. UI polish: `impeccable`. Animation: `gsap-*` skills.
10. Before marking done on non-trivial changes: consider `ponytail-review` on the diff.

## Before completion

11. Apply `quality-gates.mdc` — validate, report, update progress docs, **commit**.

## Pre-installed skills

See [skills-manifest.json](skills-manifest.json) for the full list.

## Companion repos

- [cursor-config-coding](https://github.com/Vinayak-RZ/cursor-config-coding) — source of the vendored `.cursor/`
- [cursor-config-buisness](https://github.com/Vinayak-RZ/cursor-config-buisness) — PM/GTM/research
- [cursor-config-design](https://github.com/Vinayak-RZ/cursor-config-design) — decks, video, visual
