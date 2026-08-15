# Contributing to Superdeterminism

This repository is **docs-first**. There is no simulator or adapter code yet. The useful contribution is making the research contract sharper: landscape claims, ingest mapping, methodology limitations, and ADRs.

## Cursor config

Rules and skills come from the vendored [cursor-config-coding](https://github.com/Vinayak-RZ/cursor-config-coding) tree under `.cursor/`. Read [AGENTS.md](AGENTS.md) first. Prefer updating the upstream config repo, then re-vendor and bump [`.cursor/VENDOR.md`](.cursor/VENDOR.md), over editing a one-off copy here.

Vendor guides live in [docs/cursor-config/](docs/cursor-config/), not in `docs/` root.

## Before you write

1. Read [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md), [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), and [AGENTS.md](AGENTS.md).
2. After Phase A lands, also read `docs/overview.md` and `docs/landscape.md`. Until those files exist, use the claim-hygiene list in AGENTS.md.
3. Do not claim whitespace that landscape (or AGENTS.md) marks as **unsafe**.
4. Differentiation must stay: counterfactual *re-typing* of nodes on ingested production graphs — not “score the path you already ran,” and not “search a new workflow from scratch.”

## Docs

- Keep each research doc under ~400 lines. Put citations in `docs/references.md` once it exists.
- Date any landscape or spec claim. OpenTelemetry GenAI conventions are **Development**; pin a commit, not a tag.
- Advisor-owned fields live in `advisor.*` / `det.*`. Never invent `gen_ai.*` keys.
- Methodology docs must label estimators as interventional, observational, or proxy, and must say **simulation ≠ production**.
- Do not add README links to files that are not in the tree yet.

## Decisions

Record significant choices in [DECISIONS.md](DECISIONS.md). Formal ADRs go in `docs/decisions/` once that directory exists:

- Context
- Decision
- Consequences
- Alternatives

Do not silently override an existing ADR. Propose a new one or amend the old one in the same PR.

## Plans

Non-trivial work uses [nawab-plans](.cursor/skills/nawab-plans/SKILL.md). Do not invent a thinner plan format. Do not start product code without a separate approved project-mode plan.

## Code (later)

Code conventions, test requirements, and adapter pins will land with the first implementation PR. Until then, do not add a package skeleton “for later” unless an ADR asks for it.

## License

Contributions are under the Apache License 2.0. See [LICENSE](LICENSE).
