# Contributing to Superdeterminism

This repository is **docs-first**. There is no simulator or adapter code yet. The useful contribution right now is making the research contract sharper: landscape claims, ingest mapping, methodology limitations, and ADRs.

## Before you write

1. Read [docs/overview.md](docs/overview.md) and [docs/landscape.md](docs/landscape.md).
2. Do not claim whitespace that the landscape doc marks as **unsafe**.
3. Differentiation must stay: counterfactual *re-typing* of nodes on ingested production graphs — not “score the path you already ran,” and not “search a new workflow from scratch.”

## Docs

- Keep each doc under ~400 lines. Put citations in [docs/references.md](docs/references.md).
- Date any landscape or spec claim. OpenTelemetry GenAI conventions are **Development**; pin a commit, not a tag.
- Advisor-owned fields live in `advisor.*` / `det.*`. Never invent `gen_ai.*` keys.
- Methodology docs must label estimators as interventional, observational, or proxy, and must say **simulation ≠ production**.

## Decisions

Non-trivial product choices go in [docs/decisions/](docs/decisions/) as ADRs:

- Context
- Decision
- Consequences
- Alternatives

Do not silently override an existing ADR. Propose a new one or amend the old one in the same PR.

## Code (later)

Code conventions, test requirements, and adapter pins will land with the first implementation PR. Until then, do not add a package skeleton “for later” unless an ADR asks for it.

## License

Contributions are under the Apache License 2.0. See [LICENSE](LICENSE).
