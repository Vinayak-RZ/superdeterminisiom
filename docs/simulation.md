# Simulation (L0)

**Dated 2026-08-15.** How Superdeterminism enumerates paths, finds the common ones, and splices counterfactuals. Not a live replay engine.

**Simulation ≠ production.** L0 tape splice is confirmatory evidence for a *recommended* role flip. It is not a production A/B and not L2 `do_policy`.

## What “extensive simulation” means here

From ingested traces only — every observed hop, not invented tails:

1. **Path census** — every observed hop sequence, with `n`, `p`, Wilson lower bound, errors, tokens.
2. **Transitions** — `p(next | node)` for the architecture graph.
3. **Decision points** — nodes where paths actually split (`fan_out`, outgoing entropy, modal next, visit rate).
4. **Common prefixes** — where traces still agree, and where they diverge.
5. **Common vs rare** — modal path, path entropy, singleton paths, cyclic traces.
6. **Observational notes** — census → lattice *hints* (`dominant_path`, `stable_split`, `cycle`, `error_concentrated`, …). These explain the tape. They do **not** override `recommend`.
7. **Tape-splice counterfactuals** — for each non-ABSTAIN recommendation (and the orchestrator action), rewrite the *recorded* sequences as if that role flip were already in the graph.
8. **Ranked L0 improvements** — valid splices ordered by entropy drop, then mode-mass gain. That is the “which flip would concentrate the architecture” answer.

We do **not** call a model. Live L1 tail is still not implemented. L2 roll-forward is still confirmation-tier, not default. Unobserved paths are out of scope: enumerating them would be inventing a graph.

## Levels (do not mix)

| Level | This file |
|---|---|
| L0 tape splice | **yes** — mutate the recorded path; serve the rest from the observed cassette |
| L1 hybrid fork | no live tail |
| L2 policy swap | no |

Estimator label: `observational_l0_tape_splice`.

## Splice rules

| Action | Rewrite |
|---|---|
| `FlipToRouter` / `FlipOrchestratorToCode` | After the node, attach the **modal observed suffix** |
| `FlipToWorkflow` / `FlipToDet` | Collapse every trace onto the **modal full path** |
| `BoundOrchestrator` | Drop immediate revisits; cap length at 8 |
| `CollapseOrchestrator` | Keep the first hub visit only |
| `STRENGTHEN_SDB` / `StrengthenOrchestrator` | Insert `{node}_gate` before the sensitive hop |
| `FlipToSubagent` | No hop-id change (context isolation) — splice `valid=false` if paths are identical |
| `FlipToNondet` | Cannot invent a stochastic tail — splice `valid=false` |
| `ABSTAIN` | No splice |

A splice is **invalid** when the rewritten suffix was never observed (cassette miss), or when the rewrite does not change any path. Collapsed-to-modal-path splices are marked valid but the report says a canary is still required. Invalid splices are excluded from `ranked`.

## How this improves the architecture

`recommend` still owns the lattice (Wilson, `n_min`, hard overrides). Simulation answers the path questions:

- Which sequences actually run, and how often?
- Where does control flow split, and is that split stable?
- If we applied a recommended flip, how would the *observed* path distribution change (entropy, unique paths, mass on the mode)?

Use `ranked[0]` as the highest-leverage *valid* L0 splice, then apply only after a human + canary. Do not treat ranking as an auto-apply order.

## CLI

```bash
python -m superdeterminism simulate traces.json --stdout json
python -m superdeterminism recommend traces.json --stdout json   # includes simulation
```

`recommend` and `simulate` share the same census. Agents: `--stdout json`.

## What we will not claim

- That the modal path is the only path that will run after a refactor
- That L0 is an interventional A/B
- That we enumerated paths the system *could* take but never took (that needs L1/L2)
- That observational notes replace `recommend`
- Bit-exact replay (temperature 0 is not a seed)

Methodology: [methodology.md](methodology.md). Lattice: [type-lattice.md](type-lattice.md). ADR: [0006-l0-path-simulation.md](decisions/0006-l0-path-simulation.md).
