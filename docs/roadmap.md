# Roadmap

## v0 (this research contract, then a later product plan)

- LangGraph / LangChain 1.x adapter only
- Read-only OTLP ingest
- Architecture map (`node_kind`, `det.class`)
- Offline L0 recommendations as a report
- Optional scaffold (not auto-apply)

## Explicit non-goals (v0)

- Live agent control
- Production-LLM re-runs by default (L2)
- CrewAI / MAF adapters
- Auto-merge PRs
- Wrapping CAR / Tracefork / counterfact as hard dependencies (needs its own ADR)
- Renaming the GitHub repository

## Open risks

- GenAI semantic conventions are **Development**. Schema must track commits, not assume stability.
- L0 estimates can look more confident than they are. ABSTAIN is first-class.
- Distribution shift after refactor is the large validity threat. Canary is confirmatory.
- Adjacent tools will keep shipping. Re-date [landscape.md](landscape.md) before claiming whitespace.
- Validating that recommendations improve real systems needs pilot users in staging.

## After v0 (not scheduled)

- L1 hybrid fork for high-EV candidates
- CrewAI adapter
- MAF ingest (only with a dedicated mapper)
- Planted-truth CI gate as a product feature
- Spec Kit `.specify/` for the simulator
- CI + Cloud Agent environment build

Product code does **not** start from this document. It needs a separate approved project-mode nawab plan.
