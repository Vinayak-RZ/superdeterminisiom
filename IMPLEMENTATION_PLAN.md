# P4 L0 path simulation — nawab execution contract

Approved: plan then implement without waiting. Authority: [docs/methodology.md](docs/methodology.md) (L0 tape splice). Not L1 live tail. Not L2 `do_policy`.

---

## §0 Metadata

| Field | Value |
|-------|-------|
| **Mode** | feature |
| **Branch** | `cursor/p4-path-simulation-329f` |
| **Base** | `cursor/p3-architecture-lattice-329f` |
| **Estimator** | observational L0 + tape-splice counterfactual |

---

## §1 Objective

Make simulation first-class: enumerate **all observed paths**, rank common vs rare, build the transition graph, then **L0-splice** each non-ABSTAIN recommendation to show how the path distribution would change. Architecture advice stays evidence-backed.

**Non-goals:** live L1, L2 roll-forward, inventing `gen_ai.*`, auto-apply, claiming the splice is a production A/B.

---

## §2 Deliverables

- `src/superdeterminism/simulation.py` — census, decision points, splices, ranked improvements
- `simulation` block on recommend JSON/MD
- `python -m superdeterminism simulate TRACE.json` — same census + CFs
- `docs/simulation.md` + ADR 0006
- Tests for census, decision points, modal path, splice validity, cassette miss

---

## §3 Splice rules (honest)

| Action | Tape splice |
|--------|-------------|
| FlipToRouter / FlipOrchestratorToCode | After the node, attach the modal observed suffix |
| FlipToWorkflow / FlipToDet | Collapse every trace onto the modal full path (predefined path) |
| BoundOrchestrator | Drop immediate revisits; cap length |
| CollapseOrchestrator | Keep first hub visit only |
| Strengthen* | Insert `{node}_gate` before the sensitive hop |
| FlipToSubagent / ABSTAIN | No hop-id rewrite; mark splice `valid=false` if no path change |

Invalid once the chosen suffix was never observed after that prefix (cassette miss).
