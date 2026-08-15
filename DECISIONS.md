# Decisions

Index of significant choices. Formal ADRs land in `docs/decisions/` during Phase A.

| ID | Decision | Status | Record |
|---|---|---|---|
| D0 | Project name Superdeterminism; repo URL `superdeterminisiom` unchanged | accepted | this file |
| D1 | Apache-2.0 license | accepted | [LICENSE](LICENSE) |
| D2 | Vendor cursor-config-coding into `.cursor/` (copy, not symlink) | accepted | [.cursor/VENDOR.md](.cursor/VENDOR.md) |
| D3 | Vendor guides live under `docs/cursor-config/` | accepted | this file |
| D4 | Ingest OTLP; Advisor fields in `advisor.*` / `det.*` | accepted, ADR pending | Phase A `docs/decisions/0001-otel-ingest.md` |
| D5 | v0 simulation is offline L0; no production-LLM re-run by default | accepted, ADR pending | Phase A `docs/decisions/0002-v0-offline-first.md` |
| D6 | Report + optional scaffold; never auto-apply | accepted, ADR pending | Phase A `docs/decisions/0003-no-auto-apply.md` |
| D7 | Product code requires a later project-mode nawab plan | accepted | [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) |

## D0 — Naming

- **Context:** GitHub repo is `superdeterminisiom`. Working title was Determinism Advisor.
- **Alternatives:** Rename the GitHub repo; drop Superdeterminism; use only Determinism Advisor.
- **Selected:** Keep the repo URL. Project name is Superdeterminism. Capability name is Determinism Advisor.
- **Rationale:** Avoids a rename mid-research. Names are documented in README and AGENTS.md.

## D1 — License

- **Context:** Greenfield OSS methodology tool.
- **Alternatives:** MIT; unlicensed.
- **Selected:** Apache-2.0.
- **Rationale:** Patent grant; matches MLflow / DeepEval in the adjacent eval space.

## D2 — Cursor config vendor

- **Context:** Cloud Agents load `.cursor/skills` from the cloned app repo, not from a local junction.
- **Alternatives:** Git submodule + symlink; document-only pointer to cursor-config-coding.
- **Selected:** Copy `.cursor/` into this repo and pin the source commit.
- **Rationale:** cursor-config-coding’s own cloud-agent docs require committed files.

## D3 — Vendor doc location

- **Context:** Mixing SPEC_KIT / MCP guides with Superdeterminism research confused the doc map and created links to files that looked like product docs.
- **Alternatives:** Leave vendor guides in `docs/`; put them under `.cursor/docs/`.
- **Selected:** `docs/cursor-config/`.
- **Rationale:** Keeps research `docs/*.md` for the product contract only.

## D4–D6

Accepted in research; written as ADRs in Phase A so the decision text and the ingest/methodology docs stay aligned.

## D7 — No product code in this plan

- **Context:** Temptation to scaffold a Python package “for later.”
- **Alternatives:** Scaffold now; implement v0 in the same plan.
- **Selected:** Docs-only. Simulator needs a new approved project-mode plan.
- **Rationale:** nawab + ponytail: do not invent a package without an ADR and an approved plan.
