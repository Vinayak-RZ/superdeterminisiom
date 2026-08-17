# ADR 0006 — L0 path census is the extensive-simulation contract

- **Status:** accepted
- **Date:** 2026-08-15
- **Index:** [DECISIONS.md](../../DECISIONS.md)

## Context

Architecture advice without path evidence is a lint. Users need to see every observed path, the common ones, where control flow splits, and how a recommended role flip would change that distribution. Adjacent tools already do live replay (CAR, Tracefork) or graph search (MaAS, AFlow). We must not pretend L0 is those products.

## Alternatives

- Live L1 / L2 `do_policy` as the default “extensive simulation”
- Invent unobserved tails so the census looks complete
- Ship census-only with no counterfactual splice
- Enumerate observed paths, splice recommended flips on the tape, rank valid splices

## Decision

**Extensive simulation in v0 is observational L0:** path census + decision points + tape-splice counterfactuals + ranked valid splices. Estimator: `observational_l0_tape_splice`. Live L1 remains unimplemented. L2 stays confirmation-tier. Insights explain the tape; they do not override `recommend`.

## Rationale

The differentiator is re-typing roles on an ingested graph. Path enumeration is how we *see* that graph. Splicing the recommended flip is how we show the architectural consequence without calling a model or inventing hops. Cassette-miss → `valid=false` keeps the claim honest.

## Consequences

- `simulate` CLI and the `simulation` block on `recommend` share one engine
- Invalid splices (cassette miss, no path change, FlipToNondet) are excluded from `ranked`
- Docs must keep saying simulation ≠ production
- Spec: [simulation.md](../simulation.md)
