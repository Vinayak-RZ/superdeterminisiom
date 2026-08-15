# Learning

Phase notes per [learn-while-building](.cursor/skills/learn-while-building/SKILL.md). Two to four bullets each.

## Phase R — Revise done work (2026-08-15)

- A README that links files that do not exist is a documentation bug, not a roadmap. [documentation.mdc](.cursor/rules/documentation.mdc) requires the front door to match the tree.
- nawab + documentation.mdc want root `PROJECT_OVERVIEW.md` and `DECISIONS.md` even on a docs-only repo. A thin `PROGRESS.md` is not enough.
- Vendoring cursor-config-coding into `docs/` mixed two audiences. Moving guides to `docs/cursor-config/` and fixing every relative link in rules/skills was the real cost of the move.
- extensive-readme must skip empty API/test/deploy sections. Inventing a CLI here would violate the skill’s “do not invent features” rule.

## Phase A — Research docs (2026-08-15)

- The useful product sentence is narrower than “counterfactual simulation.” CAR already owns `do_policy`; our gap is *re-typing* the node, not intervening on a step.
- OTel GenAI is usable as interchange and unusable as a domain model: no determinism class, no handoff, conditional edges often have no span. `advisor.*` / `det.*` are mandatory.
- L0 is honest only if ABSTAIN is first-class. A report that always recommends a flip would be a judge in disguise.
- LangGraph v0 is `create_agent` + `langgraph_node`, not the word “agent” and not deprecated `create_react_agent`.

## Phase N — Validate (2026-08-15)

- S2 found zero FIX-class claim-hygiene hits and no broken relative links. The “do not say” sentences are easy to grep as false positives; keep them in dedicated sections.
- Front-door links only work if you wait until the files exist (Phase R) and then re-link (commit 7). Doing both at once is how the first README went stale.
- Research docs stayed well under 400 lines because citations live in `docs/references.md`.
