# ADR 0002 — v0 offline-first (L0 before live L2)

- **Status:** accepted
- **Date:** 2026-08-15
- **Index:** [DECISIONS.md](../../DECISIONS.md) D5

## Context

A true architectural flip is CAR `do_policy` with \(K\) live roll-forwards. That costs production tokens, mutates tools if replayed live, and still is not a production A/B test.

## Alternatives

- L2-first: re-run the user’s model on every candidate
- Judge-only: ask an LLM which nodes should be tools
- Offline L0 / historical variance, L1 only for high-EV divergence

## Decision

v0 default: **no production-LLM re-runs**. Historical variance + synthesized \(f_v\) + L0 tape splice. ABSTAIN when the cassette diverges. L1 is optional and gated. L2 is confirmation, not the default.

## Rationale

Cost, safety (mutating tools), and honesty. Judge-only attribution is correlational (Who&When ~14%). CAR exists because that fails.

## Consequences

- Reports must lead with limitations and intervals.
- Some high-value flips will ABSTAIN until the user opts into L1.
- We will be accused of “not really simulating.” The answer is in [methodology.md](../methodology.md): we say so.
