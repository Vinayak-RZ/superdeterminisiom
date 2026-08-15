# Learning

Phase notes per [learn-while-building](.cursor/skills/learn-while-building/SKILL.md). Two to four bullets each.

## P3 — Role lattice + orchestrator (2026-08-15)

- The domain model already had `workflow` / `subagent` / `router`. The gap was `_decide()` collapsing them to tool-vs-LLM. Expanding actions is smaller than inventing a new graph model.
- FlipToDet must stay the lower rung when output is mode-stable. Otherwise a one-node stable classifier becomes FlipToWorkflow and every existing fixture breaks.
- The orchestrator is a report-level object, not a seventh `node_kind`. Competing roots ABSTAIN on the hub and still recommend leaves.
- `p_path` and `p_next` are the load-bearing new estimators. Output-only `p_mode` cannot justify a workflow or code-router flip.

## Leftover polish + README (2026-08-15)

- A P2 deliverable marked YAGNI (CI, canary text) is still a leftover feature once the repo is meant to be used. Shipping them does not require a new product tier.
- Trending technical READMEs win on badges + 30-second quickstart + mermaid + comparison table. Engagement bait and fake GIFs would violate extensive-readme’s “do not invent features.”
- Canary belongs on the report payload, not as a CLI apply command. The moment it becomes a button, ADR 0003 is broken.
- CONTRIBUTING still said “docs-first, no simulator.” Front-door drift is the same class of bug as linking files that do not exist.

## P2 — Ecosystem adapters (2026-08-15)

- `resolve()` treated “not in `_EXTRAS`” as “extra missing.” Custom/Langfuse/MAF need the opposite: missing extras entry means no extra required.
- Pluggability is a file a third party can copy (`examples/custom_adapter.py`), not a Protocol with one implementation. The Protocol is justified only because custom is the second adapter.
- `--adapter langgraph` must refuse MAF by attribute, not by hoping the caller picked the right flag. Silent remap is the failure mode the agnostic core was built to avoid.
- `--opt-in-l1` is a warning plus a `call_model` symbol tests can watch. A live tail is a later slice; shipping a network client now would violate ponytail and claim hygiene.

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

## P0 — Agnostic core (2026-08-15)

- Splitting “LangGraph first” vs “agnostic core first” is the load-bearing product decision. Core with zero framework deps is the only way P2 (CrewAI / MAF / raw agents) stays honest.
- Agents need JSON stdout and exit-2-on-bad-input more than they need a pretty TUI.
- `n_min=30` plus Wilson lower-bound stops a 30-identical-JSON fixture from looking more confident than it is when n is small; tests pass `--n-min` explicitly.

## P1 — LangGraph adapter (2026-08-15)

- The mapper does not need to import LangChain. Pins + `find_spec` are enough for `--adapter langgraph` presence; attribute rewrite is the whole adapter.
- Python binds `adapters.langgraph` onto the parent package after a submodule import. “Lazy” is “`__init__.py` does not import it,” not “`sys.modules` stays empty.”
- `create_react_agent` as a forbidden *token* in `src/` fights the “do not use this API” warning. Say “deprecated ReAct prebuilt” in docs; keep the token out of source and out of emitted diffs.
- Extras-on pytest skips the missing-extra exit-2 tests. Both modes are required: extras-free for that path, extras-on for `--adapter langgraph` end-to-end.

## P1 / P2 specs (2026-08-15)

- Specifying adapters *before* code is what keeps the core honest: P1 is allowed one LangGraph file; P2 is when a `Protocol` is justified (second adapter).
- P1 must not fork the recommender. If the mapper cannot produce P0 `Trace`s, the adapter is wrong — not the decision rules.
- P2 “done” is pluggability (custom example + at least one non-Lang path), not “we ingested one more Lang sink.”

## Phase N — Validate (2026-08-15)

- S2 found zero FIX-class claim-hygiene hits and no broken relative links. The “do not say” sentences are easy to grep as false positives; keep them in dedicated sections.
- Front-door links only work if you wait until the files exist (Phase R) and then re-link (commit 7). Doing both at once is how the first README went stale.
- Research docs stayed well under 400 lines because citations live in `docs/references.md`.
