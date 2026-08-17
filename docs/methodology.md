# Methodology

How Superdeterminism estimates a **role flip** (including determinism-class and orchestrator actions). This is a citable design, not a guarantee. Lattice: [type-lattice.md](type-lattice.md). Hub: [orchestrator.md](orchestrator.md).

**Simulation ≠ production.** The only confirmatory estimator is a canary with the same outcome vector. Every number in a v0 report is an estimate with a confidence interval, or we **ABSTAIN**.

## What a flip is

A node \(v\) has a determinism class \(\delta(v)\). The intervention is CAR’s `do_policy` ([Shah 2026, arXiv:2606.08275](https://arxiv.org/abs/2606.08275)):

```text
FlipToDet(v):         replace stochastic policy π_v(· | s) with a function f_v(s)
FlipToNondet(v):      replace deterministic function f_v(s) with a stochastic policy
FlipToWorkflow(v):    replace an open loop with a predefined code path
FlipToSubagent(v):    isolate the hop; child returns one structured result
FlipToRouter(v):      replace model-chosen next-hop with a classifier / code edge
BoundOrchestrator:    add a hard step/turn/token cap in code
FlipOrchestratorToCode: replace an LLM supervisor with a code router / DAG
```

These are *policy interventions* ([Pearl 2009](https://doi.org/10.1017/CBO9780511803161)), not log inspection. After the swap, everything downstream re-decides. Because policies are stochastic, one intervention yields a **distribution** over outcomes, never a single path.

The unit of intervention is the **decision mechanism**, not the side-effecting call. Flipping `issue_refund` does nothing if the LLM already committed one step earlier. Use CAR’s **point-of-commitment** rule: the latest step whose interval still excludes zero.

## Three nested counterfactuals

Do not mix these levels.

| Level | What you did | What you may claim |
|---|---|---|
| **L0 tape splice** | Mutate one recorded I/O blob; serve the rest from a hash-verified cassette | Partial CF, near-zero cost. Invalid once the next call-site misses. |
| **L1 hybrid fork** | Replay prefix; live-execute the divergent tail | Same agent code, new tail. Costs the tail. |
| **L2 policy swap** | Replace the mechanism and roll forward \(K\) times | Architectural `do(·)`. Confirmation tier, not v0 default. |

v0 estimates Pearl **rung 2** (intervention). It never claims rung 3 (“this exact incident would have gone the other way”).

LangGraph time-travel is **checkpoint-restart**, not VCR ([docs](https://docs.langchain.com/oss/python/langgraph/use-time-travel)). Replay re-executes nodes; LLM calls fire again. Use checkpoints as the graph-shaped index; use a tape at the HTTP seam as the I/O record.

## Residual nondeterminism

Hosted temperature-0 is not a seed. Thinking Machines measured 80 unique completions in 1000 greedy runs ([Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)). CAR reports `action_match_rate` as residual nondeterminism. We never promise bit-exact architecture advice from a single replay.

## v0 algorithm (default: no production-LLM re-runs)

Label every estimator: **interventional**, **observational**, or **proxy**.

1. Reconstruct \(G\). Build a hash-verified tape (Tracefork / AgentReplay style). Abort if verify fails.
2. **Observational / proxy:** historical variance as a coarsened `do_resample` (canonicalized keys, \(p_{\mathrm{mode}}\), \(p_{\mathrm{path}}\), \(p_{\mathrm{next}}\), entropy, Wilson CIs). Stratify by model / prompt / graph version. Require \(n_{\min} = 30\). Output-only \(p_{\mathrm{mode}}\) is not enough for workflow / router / orchestrator-to-code.
3. Synthesize \(f_v\) from majority vote, schema check, or a user-supplied function. Coverage is first-class — most wins are **hybrids** (function + LLM fallback).
4. **L0 splice.** If the tail stays cassette-stable, you have a bound. If it diverges, stop and say so.
5. Optional cheap judge on recorded I/O, gated on Cohen’s \(\kappa \ge 0.8\). Never use a judge for *attribution* (Who&When step-level accuracy is ~14%; that is why CAR exists).
6. Spend **L1** only on divergent, high-EV candidates. **L2** and live Shapley are off by default.
7. Planted-truth fixtures (DET-vs-open-ended) before any customer-facing number.

WHEN2TOOL ([arXiv:2605.09252](https://arxiv.org/abs/2605.09252)) can estimate *whether a tool is needed* more confidently than *whether a flip helps*. Probes are open-weights only. v0 may cite necessity as supporting evidence, not as the flip delta.

## Outcome vector \(Y\)

| Metric | Why it is in \(Y\) |
|---|---|
| Cost | Tokens + tool $ |
| Latency | User-visible and SLO |
| Failure rate | Task / policy / schema |
| Output variance | \(p_{\mathrm{mode}}\), entropy |
| Auditability | Can a human replay the decision from logs alone? |
| Policy compliance | Commit / spend / PII / auth gates |

Do not collapse \(Y\) to a single score in the report. Show per-metric deltas with intervals.

## Decision rules

Prefer the **lowest** Anthropic rung the tape supports. Full table: [type-lattice.md](type-lattice.md).

**FlipToDet** when the output is schema-shaped (`schema_ok ≥ 0.80`) and \(p_{\mathrm{mode}}\) + Wilson ≥ `0.70`. This is the lower rung when a hop is already a function.

**FlipToWorkflow** when path *shape* is stable (`p_path` + Wilson ≥ `0.70`), path length ≥ 3, and this hop’s output is *not* mode-stable (else FlipToDet).

**FlipToRouter** when next-hop id is mode-stable (`p_next` + Wilson ≥ `0.70`).

**FlipToSubagent** when a nested checkpoint ns has a structured return but unstable output — isolate context.

**Hard override:** policy / commit / spend / PII / auth nodes become deterministic gates regardless of accuracy (proposer, verifier, commit, reject). If the *hub* reaches those leaves ungated, that is `StrengthenOrchestrator`.

**FlipToNondet** only when a DET node’s unhandled tail is the failure cluster, judgment actually flips those failures, **and** the new LLM is wrapped in that four-part gate. Bare FlipToNondet of a commit path is forbidden.

**STRENGTHEN_SDB** (keep the proposer, harden the gate) is a first-class recommendation, not a consolation prize.

**ABSTAIN** when the primary-metric CI includes the threshold, coverage is incomplete, the graph was scraped, L0 diverged and L1 was not run, or \(n < n_{\min}\).

## Threats the report must attach

Confounding in historical variance; selection on the current architecture’s traffic; **distribution shift after refactor** (the large one); cassette-hit ≠ production-hit; judge noise; mutating-tool replay as a real side effect; Goodharting the advisor with JSON wrappers; quoting fixture top-1 as product accuracy.

LLM-as-judge attribution is correlational. Do not ship a report that only says “the model thinks this step caused it.”

ADR: [0002-v0-offline-first.md](decisions/0002-v0-offline-first.md).
