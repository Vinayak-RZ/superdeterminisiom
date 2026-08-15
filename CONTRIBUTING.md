# Contributing to Superdeterminism

This repository is a **working advisor** (P0 core + P1/P2 adapters) plus the research contract that keeps claims honest. Useful contributions: sharper landscape/ingest/methodology docs, extras-free tests, or an adapter that returns `list[Trace]` without forking the recommender.

## Cursor config

Rules and skills come from the vendored [cursor-config-coding](https://github.com/Vinayak-RZ/cursor-config-coding) tree under `.cursor/`. Read [AGENTS.md](AGENTS.md) first. Prefer updating the upstream config repo, then re-vendor and bump [`.cursor/VENDOR.md`](.cursor/VENDOR.md), over editing a one-off copy here.

Vendor guides live in [docs/cursor-config/](docs/cursor-config/), not in `docs/` root.

## Before you write

1. Read [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md), [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), and [AGENTS.md](AGENTS.md).
2. Read [docs/overview.md](docs/overview.md) and [docs/landscape.md](docs/landscape.md).
3. Do not claim whitespace that landscape (or AGENTS.md) marks as **unsafe**.
4. Differentiation must stay: counterfactual *re-typing* of nodes on ingested production graphs — not “score the path you already ran,” and not “search a new workflow from scratch.”

## Docs

- Keep each research doc under ~400 lines. Put citations in [docs/references.md](docs/references.md).
- Date any landscape or spec claim. OpenTelemetry GenAI conventions are **Development**; pin a commit, not a tag.
- Advisor-owned fields live in `advisor.*` / `det.*`. Never invent `gen_ai.*` keys.
- Methodology docs must label estimators as interventional, observational, or proxy, and must say **simulation ≠ production**.
- Do not add README links to files that are not in the tree yet.
- When behaviour changes, update [README.md](README.md) and [docs/usage.md](docs/usage.md) in the same PR.

## Decisions

Record significant choices in [DECISIONS.md](DECISIONS.md). Formal ADRs go in [docs/decisions/](docs/decisions/):

- Context
- Decision
- Consequences
- Alternatives

Do not silently override an existing ADR. Propose a new one or amend the old one in the same PR.

## Plans

Non-trivial work uses [nawab-plans](.cursor/skills/nawab-plans/SKILL.md). Do not invent a thinner plan format.

## Code

- Core lives in `src/superdeterminism/`. **No LangChain / LangGraph / CrewAI imports in core.**
- Adapters are lazy. Register in `adapters/__init__.py`. Copy [examples/custom_adapter.py](examples/custom_adapter.py) for a house orchestrator.
- `python -m pytest -q` must pass extras-free (`pip install -e ".[dev]"`).
- CLI stays non-interactive (JSON in/out) so agents can drive it.
- Do not auto-apply refactors. Do not emit `create_react_agent`.
- Do not ship a live L1 network client without an explicit plan. `SUPERDETERMINISM_L1_MODEL` is reserved.

## License

Contributions are under the Apache License 2.0. See [LICENSE](LICENSE).
