# Type lattice

**Dated 2026-08-15.** What Superdeterminism may re-type. Doctrine: [agent-architectures.md](agent-architectures.md). Hub object: [orchestrator.md](orchestrator.md). Estimators: [methodology.md](methodology.md).

A **determinism-class** flip (tool ↔ LLM) is one *axis*. The product is the whole lattice.

## Two node axes + one graph object

| Axis | Field | Values |
|---|---|---|
| Role | `node_kind` | `workflow`, `subagent`, `router`, `deterministic_tool`, `retriever`, `llm_reasoner` |
| Mechanism | `det.class` | `deterministic`, `llm`, `llm_seeded`, `stochastic_index`, `composite`, `external` |
| Control | `orchestrator` (report block) | envelope + metrics + action |

`node_kind` is a versioned internal enum. Never persist raw `gen_ai.operation.name` as the contract. Advisor fields: `advisor.*` / `det.*`. Never invent `gen_ai.*`.

## Node actions

JSON keeps `FlipToDet` as the wire value for “collapse this hop to a tool.” Docs may say CollapseToTool.

| Action | From (typical) | To | When (observational L0) |
|---|---|---|---|
| `FlipToDet` | LLM / subagent | `deterministic_tool` | `schema_ok ≥ 0.80` and `p_mode` + Wilson ≥ `0.70` |
| `FlipToWorkflow` | LLM / subagent / ReAct envelope | `workflow` | Path *shape* stable (`p_path` + Wilson ≥ `0.70`), path length ≥ 3, this hop’s *output* is not mode-stable (else FlipToDet is the lower rung) |
| `FlipToSubagent` | LLM hop | `subagent` | Nested checkpoint ns, structured return (`schema_ok ≥ 0.80`), output not mode-stable, isolation would shrink parent context |
| `FlipToRouter` | LLM hop | `router` | Next-hop id is mode-stable (`p_next` + Wilson ≥ `0.70`); payload may vary |
| `FlipToNondet` | DET tool | `llm_reasoner` | `failure_rate ≥ 0.30`, not sensitive, wrap proposer/verifier/commit/reject |
| `STRENGTHEN_SDB` | any sensitive | gate stays DET | Name matches refund/commit/payment/auth/PII/… |
| `ABSTAIN` | any | unchanged | `n < n_min`, Wilson includes the threshold, or no rule fires |

Prefer the **lowest** Anthropic rung the tape supports. Output-only `p_mode` is not enough for `FlipToWorkflow` or `FlipToRouter`. Those need path-shape / next-hop CIs.

## Path-shape vs output-shape

| Estimator | What is canonicalized | Used for |
|---|---|---|
| `p_mode` | Node output JSON | `FlipToDet` |
| `p_path` | Ordered `node_id` sequence per trace | `FlipToWorkflow` |
| `p_next` | Next `node_id` after this hop | `FlipToRouter`, `FlipOrchestratorToCode` |

All three use Wilson lower bounds. Default `n_min = 30`. If the lower bound is below the threshold, **ABSTAIN** even when the point estimate looks good.

## What a flip is (still `do_policy`)

CAR’s intervention ([Shah 2026](https://arxiv.org/abs/2606.08275)) still applies. Re-typing a *role* is a policy swap at the decision node, not a log rewrite. After the swap, downstream re-decides. One intervention yields a **distribution**.

Point-of-commitment: flip the latest step whose interval excludes zero, not the side-effecting descendant.

## Hard overrides

Unchanged: commit / spend / PII / auth names stay deterministic gates. Bare `FlipToNondet` of a commit path is forbidden. If the *hub* reaches those leaves with no intervening DET gate, that is `StrengthenOrchestrator` ([orchestrator.md](orchestrator.md)), not a leaf FlipToNondet.

## Non-goals on this lattice

- `FlipToRAG` / `SwapModel` until traces can support them without guessing
- Searching a new graph (MaAS / AFlow)
- Linting files without traces
- Invented `gen_ai.agent.handoff.*`
