# ADR 0003 — Report + optional scaffold; never auto-apply

- **Status:** accepted
- **Date:** 2026-08-15
- **Index:** [DECISIONS.md](../../DECISIONS.md) D6

## Context

A flip changes production control flow. Auto-applying a patch or opening a PR would be an irreversible agent action on someone else’s graph.

## Alternatives

- Auto-open PRs
- Rewrite `graph.py` in place
- Report + optional scaffold the human copies

## Decision

Keep the node name, change the callable, emit `REPORT.md` and an illustrative diff. Refuse Send / Command / interrupt rewrites and in-place edits. See [refactor.md](../refactor.md).

## Rationale

agentic-system-design: checkpoint before irreversible edits. ponytail: do not invent a merge bot. counterfact’s `apply_recommendation` already shows why silent rewrites are unsafe.

## Consequences

- Adoption is slower (human copies the scaffold).
- We never claim the graph was improved — only that a change was recommended.
- Re-record after apply; old tapes are invalid.
