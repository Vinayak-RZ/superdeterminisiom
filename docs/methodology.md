# Determinism Flip Simulation: A Methodology for Determinism Advisor

**Status:** v0 design (honest, cheap, useful)  
**Product:** Determinism Advisor (working title) / superdeterminism  
**Question this document answers:** How can we *scientifically* estimate what would happen if one node in a production agent architecture were flipped from stochastic (LLM / subagent) to deterministic (tool / function), or vice versa, **without pretending that a simulation is a production A/B test**?

This document is a citable methodology, not a product spec. It synthesizes interventional agent-trace research (2025–2026), record/replay substrates, tool-necessity theory, and LangGraph’s actual checkpoint primitive. Every estimator is labeled as **interventional**, **observational**, or **proxy**. Limitations are first-class, not footnotes.

---

## 0. Problem statement

A production agent is a graph. Some nodes are stochastic policies (an LLM call, a subagent, a “reason then act” hop). Some nodes are deterministic mechanisms (a parser, a SQL query, a policy gate, a calculator, a schema validator). Teams routinely put the *wrong type* on a node:

- An LLM extracts a JSON field that a regex or Pydantic model already determines.
- A hard-coded router cannot handle novel intents that need judgment.
- A “planner” LLM is actually a policy enforcer, and policy must not be probabilistic.
- A deterministic retriever is being asked to do synthesis it cannot do.

**Determinism Advisor** takes production traces, reconstructs the architecture graph, and for *ambiguous* steps estimates the counterfactual:

> What if this node were the other type?

It then reports estimated deltas in **cost, latency, failure rate, output variance, auditability, and policy compliance**, and recommends a refactor — with confidence intervals and an explicit “this is not a production guarantee” banner.

We call the intervention a **determinism flip**.

```
FlipToDet(v):    replace stochastic policy π_v(· | s) with a deterministic function f_v(s)
FlipToNondet(v): replace deterministic function f_v(s) with a stochastic policy π_v(· | s)
```

These are *policy interventions* in Pearl’s sense ([Pearl 2009](#pearl-2009)), not mere log inspection. The rest of this document says how far we can get toward a real `do(·)` — and what to do when we cannot re-run the LLM.

---

## 1. Formal model

### 1.1 Architecture graph

Let \(G = (V, E)\) be a directed (possibly cyclic, via loops) execution graph reconstructed from traces. Each node \(v \in V\) has:

| Field | Meaning |
|---|---|
| \(\tau(v) \in \{\mathrm{LLM}, \mathrm{SUBAGENT}, \mathrm{TOOL}, \mathrm{FUNCTION}, \mathrm{ROUTER}, \mathrm{MEMORY}, \mathrm{HUMAN}\}\) | Declared type |
| \(\delta(v) \in \{\mathrm{STOCH}, \mathrm{DET}\}\) | Determinism class. LLM/SUBAGENT default STOCH; TOOL/FUNCTION default DET; ROUTER is DET iff it is code, STOCH iff it is an LLM. |
| \(\mathrm{schema}_v\) | Input/output contract if known |
| \(\mathrm{side\_effects}(v)\) | Whether \(v\) mutates the world |

A **step** in a run is an instantiation of a node: \((v, t, s_t, a_t, o_t)\), where \(s_t\) is the decision state, \(a_t\) the action, \(o_t\) the observation.

### 1.2 Run as a structural causal model (SCM)

Following Causal Agent Replay ([Shah 2026, arXiv:2606.08275](#car-2026); [jaineet17/causal-agent-replay](https://github.com/jaineet17/causal-agent-replay)), a trajectory is

\[
\tau = \big[\, s_0,\ (a_1, o_1),\ \dots,\ (a_n, o_n),\ y \,\big]
\]

- \(s_k\): exact state the node decided from (system prompt, tool schemas, history, retrieved memory).
- \(a_k \sim \pi(\cdot \mid s_k)\) if \(\delta = \mathrm{STOCH}\); \(a_k = f(s_k)\) if \(\delta = \mathrm{DET}\).
- \(o_k\): environment / tool result.
- \(y = Y(\tau) \in [0,1]^m\): a *vector* of outcomes (not a single pass/fail). For Determinism Advisor, \(Y\) includes cost, latency, failure, variance, auditability, and policy compliance (Section 11).

This is the causal-influence-diagram program for agents ([Everitt et al. 2021, arXiv:2102.01685](#everitt-2021); [Kenton et al. 2023, arXiv:2208.08345](#kenton-2023)): the policy is a causal mechanism; effects are read off interventions, not off the surface trace.

**Why this matters for a flip.** A determinism flip is *not* “blame the step that executed the harmful tool call.” CAR’s motivating example: the `issue_refund` call is usually the mechanical consequence of a *decision* one step earlier. Flipping the refund *tool* to deterministic does nothing if the LLM already committed. The unit of intervention is the **decision mechanism**, not the side-effecting call.

### 1.3 The determinism-flip intervention

A flip at node \(v\) starting at the first occurrence \(k\) of \(v\) in \(\tau\) is a **policy swap**:

\[
\mathrm{do\_policy}(k,\ \pi'_v)
\]

where \(\pi'_v\) is either a deterministic function \(f_v\) (FlipToDet) or a stochastic policy (FlipToNondet). After the swap, *everything downstream re-decides*. Because \(\pi\) is stochastic, one intervention yields a **distribution** over outcomes, never a single path ([Shah 2026](#car-2026)).

This is strictly stronger than “replace the recorded string.” Replacing the recorded string and *replaying the cassette* (AgentReplay / Tracefork pure replay) answers a different question: *holding the rest of the recorded I/O fixed, what if this one response changed?* That is a valid **partial** counterfactual. It is not the full architectural counterfactual, because a real refactor changes what downstream nodes *ask for*.

We therefore distinguish three nested counterfactuals, and never mix their claims:

| Level | Intervention | What it answers | Cost |
|---|---|---|---|
| **L0 — Tape splice** | Replace recorded \(a_k\) or \(o_k\); serve the rest from the cassette / tape | “If this I/O blob had been different, and later calls still matched, what happens?” | \(\approx \$0\) |
| **L1 — Hybrid fork** | Splice at \(k\); replay prefix; live-execute the divergent tail | “If this node’s mechanism changed, how does the *same agent code* continue?” | Tail cost only |
| **L2 — Policy swap** | Replace \(\pi_v\) with \(f_v\) (or vice versa) and re-run from \(s_k\) under the new mechanism, \(K\) times | “If we *refactored the architecture*, what is the outcome distribution?” | \(K \times\) tail |

v0 **defaults to L0 + observational proxies**, optionally spends on L1 for a small candidate set, and treats L2 as a paid confirmation tier. Claiming L2 from L0 data is a validity error (Section 9).

### 1.4 Stochastic-deterministic boundary (SDB)

A flip is not only a node-type change. It is a change to the **stochastic–deterministic boundary**: the four-part contract by which an LLM proposal becomes a system action ([arXiv:2605.20173](#sdb-2026); [Agent Patterns Catalog — SDB](https://www.agentpatternscatalog.org/patterns/stochastic-deterministic-boundary/)):

1. **Proposer** — the LLM (or, after FlipToDet, nothing).
2. **Verifier** — a deterministic check (schema, policy predicate, proof).
3. **Commit** — the durable write, only on accept.
4. **Reject** — a typed signal back to the proposer.

An audit of five open-source frameworks found explicit verifier-and-commit logic at 19 of 21 LLM-to-action call sites; 15 of 21 published agent-failure post-mortems localized to weaknesses at this boundary ([arXiv:2605.20173](#sdb-2026)). Deterministic pre-execution gates on mutating tools raise both reliability and measured task success in permissive environments ([arXiv:2607.07405](#gates-2026)).

**Implication for flips.** FlipToDet of a *policy* or *commit* node is almost always correct: the safety floor must not be probabilistic ([PolicyLayer](https://policylayer.com/blog/deterministic-ai-agent-policies)). FlipToDet of a *proposer* is a product judgment: you are giving up coverage of novel inputs in exchange for variance collapse. v0 must score these differently (Section 12).

---

## 2. Prior art, mapped onto the flip

This section is the citation spine. Each system answers a *different* question. Determinism Advisor composes them; it does not re-derive them.

### 2.1 Causal Agent Replay (CAR) — arXiv:2606.08275

**Paper:** [Shah, J. *Causal Agent Replay: Counterfactual Attribution for LLM-Agent Failures.* arXiv:2606.08275](https://arxiv.org/abs/2606.08275)  
**Code:** [https://github.com/jaineet17/causal-agent-replay](https://github.com/jaineet17/causal-agent-replay)

CAR answers: *which step caused a failure?* by intervention, not correlation. LLM-judge attribution on the Who&When benchmark is ~14% step-level accuracy ([Zhang et al. 2025, arXiv:2505.00212](#whowhen-2025)). CAR models the run as an SCM and applies `do(·)`.

#### Intervention algebra

| Operator | Meaning | Question | Flip use |
|---|---|---|---|
| `do_resample(k)` | Re-draw \(a_k\) from the *same* policy | How sensitive is \(y\) to this step? | **Variance probe.** High flip-rate under resample ⇒ the node is a variance source. Candidate for FlipToDet if a function can pin the mode. |
| `do_action(k, a')` | Force a specific action | What if it had done \(X\)? | **Oracle splice.** Force the deterministic function’s output. |
| `do_observation(k, o')` | Replace tool result | What if the tool returned \(X\)? | FlipToNondet of a tool: inject LLM-like noisy observations. |
| `do_context(k, h')` | Edit history at \(k\) | What if the prompt hadn’t contained \(X\)? | Confounder control (injection, retrieved junk). |
| `do_policy(k, π')` | Swap the model from \(k\) onward | Did the model upgrade break it? | **The flip itself.** \(\pi' = f_v\) or \(\pi' = \mathrm{LLM}\). |

The null intervention `do_resample` is the foundation of attribution: it changes nothing except re-drawing the decision. If the bad outcome usually disappears when you resample \(k\) but persists when you resample \(k+1\), then \(k\) is the **point of commitment**.

#### Point-of-commitment (the run-forward confound)

Naive single-step effects are *total* effects through a stochastic continuation: resampling an early irrelevant step also re-rolls the genuinely pivotal step downstream, so magnitude alone cannot localize. CAR’s rule: the causal locus is the **latest** step whose effect’s confidence interval still excludes zero — the last point at which re-deciding still rescues the run.

**For flips:** recommend FlipToDet at the commitment node, not at the side-effecting descendant. Flipping the descendant is a category error.

#### Estimators and confidence intervals

- **Contrastive single-step:** hold \([0,k)\) factual, `do_resample(k)`, run forward \(K\) times, estimate \(P(\mathrm{bad} \mid \mathrm{do})\) and its shift. Wilson interval on the proportion; bootstrap interval on the difference.
- **Budget-bounded Monte-Carlo Shapley:** for AND-failures (bad only if two steps both go wrong), single-step effects either double-count (~2) or vanish (~0). Shapley averages marginal contributions over coalitions \(S\) of steps held factual, \(v(S) = P(\mathrm{bad} \mid \mathrm{held}=S)\). Antithetic reverse-permutation pairing; normal-approximation CIs. **Do not cache \(v(S)\) across permutations** — caching collapses per-step marginal variance and reports false confidence. Avoid truncated Monte-Carlo Shapley (can skip a pivotal late step). Validated on a planted two-step SCM: \(\phi_0=0.44,\ \phi_1=0.45,\ \phi_2\approx 0\); efficiency sum \(0.909\) vs analytic \(0.91\).

#### Residual nondeterminism

Faithful replay is the foundation: record every nondeterministic input so deterministic glue can re-execute; treat the model call as the one irreducible nondeterministic input; **measure** replay fidelity rather than assert it.

Hosted providers are not deterministic even at temperature 0, because inference kernels are not batch-invariant: the server’s load changes batch size, which changes reduction order in matmul / RMSNorm / attention, which changes tokens ([Thinking Machines Lab 2025](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/); [thinking-machines-lab/batch_invariant_ops](https://github.com/thinking-machines-lab/batch_invariant_ops)). On Qwen3-235B-A22B-Instruct at temperature 0, 1000 identical prompts produced **80 unique** 1000-token completions. Batch-invariant kernels collapsed this to 1.

CAR therefore reports an **action-match rate** for replay. A single-stream local model with `seed + temperature=0 + fixed num_ctx` replays far more faithfully. Current frontier hosted models may not accept a temperature parameter at all.

**v0 rule:** never claim bit-exact LLM replay against a hosted API. Report `action_match_rate`. If it is below a threshold (we suggest 0.95 for local seeded, 0.70 as a “hosted, treat as distributional” floor), all L2 effects must be labeled distributional.

#### CAR limitations we inherit

- Contrastive effect is a total effect; isolating a *direct* effect needs common random numbers across divergent LLM contexts (left open).
- Judge-based \(Y\) injects its own noise; prefer rule-based outcomes.
- Real tools with side effects are out of scope unless mocked or sandboxed.
- Shapley is exponential; the MC estimator is budget-bounded.

### 2.2 CausalFlow — arXiv:2605.25338

**Paper:** [Bonagiri et al. *CausalFlow: Causal Attribution and Counterfactual Repair for LLM Agent Failures.* arXiv:2605.25338](https://arxiv.org/abs/2605.25338)

CausalFlow answers: *which step, if replaced, flips failure to success — and what is the minimal such replacement?*

#### Typed steps

A `TraceLogger` records a sequence of typed steps with explicit dependencies:

```
REASONING | TOOL_CALL | TOOL_RESPONSE | LLM_RESPONSE | MEMORY_ACCESS | FINAL_ANSWER
```

Each step carries content and dependency indices. **Plain chain-of-thought is not an intervention surface.** CausalFlow’s structured logging cost 13.1pp of initial GSM8K accuracy (75.0% vs 88.1% Direct); repair recovered the gap. v0 must either ingest typed traces or *post-hoc type* them; untyped CoT cannot be flipped.

#### Causal Responsibility Score (CRS)

For a failed trace \(\tau\) and \(K\) intervention proposals \(\{s_i^{\prime(k)}\}\):

\[
\mathrm{CRS}(s_i) = \max_{k \in \{1,\dots,K\}} \mathbb{I}\!\left[\mathcal{V}\!\big(y(\tau[i \leftarrow s_i^{\prime(k)}]), x\big) = 1\right]
\]

\(\mathrm{CRS}=1\) iff *at least one* replacement of \(s_i\), with downstream re-execution, flips the verifier to success. Interventions are LLM-proposed minimal edits; evaluation is deterministic re-execution when an executor exists (Python interpreter) and **predictive re-execution** otherwise.

Successful repairs are ranked by **minimality** (position-wise token match with a length penalty). A three-agent consensus score mixes CRS with critic agreement.

Empirically, CausalFlow converted 42.7% of failed executions into validated minimal repairs across GSM8K, MBPP, SealQA Hard, and MedBrowseComp. \(K=3\) proposals sufficed; more did not pay.

#### Flip use

- **FlipToDet candidate:** a step with \(\mathrm{CRS}=1\) whose successful \(s_i^\star\) is *expressible as a function* (schema fill, arithmetic, tool-arg construction, policy predicate). The contrastive pair \((s_i, s_i^\star)\) *is* the specification of \(f_v\).
- **FlipToNondet candidate:** a DET node whose CRS-style replacements that *add* judgment (paraphrase a query, choose a different tool) flip failure to success — the function’s contract is too tight.
- **Do not** treat CRS as a probability. It is a max-indicator over \(K\) proposals. A CRS of 0 means “we did not find a repair,” not “the step is innocent.”

#### CausalFlow limitations we inherit

- Proposal quality is LLM-dependent; missed proposals under-identify responsibility.
- Predictive re-execution (no executor) is itself a model — simulation ≠ production.
- Retrieval-gap failures cannot be repaired by local reasoning edits.
- Noisy dependency annotations weaken intervention semantics.
- LLM-judge verification of browsing repairs had 86–91% precision in a 30-example audit; reported repair rates should be adjusted.

### 2.3 Tracefork — content-addressed tape, hash-verified replay, blame

**Code:** [https://github.com/pratik916/tracefork](https://github.com/pratik916/tracefork) (PyPI: `tracefork`)

Tracefork is a time-travel debugger: record a run to a content-addressed tape, replay it bit-exact for $0 (hash-verified), fork any step, measure causal blame with CIs.

#### Substrate (the load-bearing claim)

- **Record** at the HTTP seam (Anthropic SDK httpx; parallel botocore seam for Bedrock). Clock / id / random go through a `NondetSource`.
- **Tape:** sha256 content-addressed blobs + ordered event log, SQLite, hash-chain `digest()`.
- **Replay:** every request *body* is sha256-checked against the tape. A replay transport has **no inner transport** — an unrecorded request is a hard error, never a silent bill. No network, no key.
- **Determinism boundary (honest):** single-process (sync or asyncio), nondeterminism captured through `NondetSource`, including asyncio fan-out completion order. Agents that read `datetime.now()` / `uuid` / `random` directly, or span threads/subprocesses, step outside the boundary; the verifier *detects* drift. Opt-in `BoundaryGuard` makes this a record-time error.

This is the correct primitive for L0. LangGraph time-travel is *not* this (Section 7).

#### Fork and blame

Fork is three phases: prefix-replay ($0, asserted), mutation-injection, tail-record (the counterfactual, recorded fresh). Blame forks each step \(k\) times, grades via an `Oracle`, counts **flip-rate**, reports **Wilson-score** 95% CIs, and is budget-capped. DAG-aware Shapley and a Wilson/BH tournament API exist in later versions.

#### Validation scope (copy this honesty)

The *proven* claim is bit-exact, hash-verified replay. Causal/blame claims are validated on **controlled, labeled fixtures, not real-world traces**:

- `tracefork validate`: inject an outcome-flipping fault at any step → top-1 = 1.00; negative control enforced. Does **not** claim discrimination among competing causes.
- `tracefork bench`: 10/11 competing causes resolved; the named exception is single-ordering temporal Shapley under-crediting the earlier half of a symmetric conjunction on a strictly sequential tape.

**v0 rule:** ship a `validate` / `bench` pair with planted flips *before* publishing any accuracy number on customer traces. A plausible heatmap without planted-SCM recovery is the failure mode CAR and Tracefork both refuse.

### 2.4 AgentReplay — VCR cassette mutate

**Code:** [https://github.com/gadda00/agentreplay](https://github.com/gadda00/agentreplay)  
**Writeup:** [Ndunda, *AgentReplay: Deterministic Replay and Counterfactual Debugging*](https://victorndunda.com/blog/articles/agentreplay-deterministic-replay.html)

AgentReplay sits between the agent and every external nondeterministic thing (model API, tools, network, clock) and records a VCR-style cassette. Four modes:

| Mode | Behavior |
|---|---|
| RECORD | Call the real client; write request/response. |
| REPLAY | Look up call-site ID; return recorded response. Model is never called. Deterministic by construction. |
| HYBRID | Replay until first divergence; fall through to live. |
| LIVE | Pass-through. |

The agent’s own code never knows which mode it is in.

**Call-site IDs.** SHA-256 of `(step_id, canonicalized_input)`. Canonicalization sorts dict keys, strips `request_id` / `id` / `created` / `system_fingerprint`, redacts UUID-shaped strings and ISO-8601 timestamps. Without this, every replay diverges on the first SDK-generated id. This is the VCR / Mozilla `rr` pattern.

**`mutate_response(cassette, seq, new_response)`** forks the cassette, replaces one step, and optionally HYBRID-replays forward. This is the L0/L1 primitive for a flip: the “new response” is \(f_v(s)\) (FlipToDet) or a sampled LLM completion (FlipToNondet).

Claimed measurements: 100% bit-exact reproduction fidelity on their synthetic suite; 0.67% instrumentation overhead; 100% investigation-cost reduction in pure replay. Limitations they state (we adopt): uninstrumented side channels break bit-exactness; storage grows (content-addressed dedup + retain-failures policy); **replay does not by itself make the agent more reliable**.

Related cassette tools: [llm-rewind/rewind](https://github.com/llm-rewind/rewind) (mutation testing: drop steps, 429s, truncated responses); [vcrpy](https://github.com/vcrpy/vcrpy) / vcr-langchain (HTTP only, no agent-level mutate).

**Critical comparison with LangGraph time-travel** (from AgentReplay’s own table, which we agree with): LangGraph “replay” re-executes nodes live. LLM calls fire again and may return different results. That is checkpoint-restart, not VCR. Do not advertise LangGraph time-travel as a $0 flip simulator.

### 2.5 counterfact-labs/counterfact — Shapley ablation

**Code:** [https://github.com/counterfact-labs/counterfact](https://github.com/counterfact-labs/counterfact)

counterfact is a drop-in LangGraph `StateGraph` that attributes pipeline quality by **actually re-running** with agents ablated (replaced by no-ops) or **severely degraded** (shape preserved, content destroyed). Shapley values and leave-one-out over coalitions; quality from pluggable classifiers (or Braintrust scorers).

**Ablate vs degrade.** Pure ablation of a retriever / parser / reranker *structurally collapses* the pipeline, so the module trivially dominates attribution (“is it load-bearing?”) without telling you whether its *quality* hurts answers. Degradation keeps the shape (retriever still returns a non-empty doc list) and measures quality contribution.

**Flip use.** A FlipToDet is closer to *replace with a function* than to *ablate*. Ablation answers necessity; degradation answers quality; a flip answers *mechanism substitution*. Use counterfact’s Shapley machinery, but the removal operator for a flip is **substitute**, not ablate:

```
coalition S: nodes in S run as today
nodes not in S: run as the flipped mechanism (f_v or π_v), not as no-ops
v(S) = E[Y | mechanisms]
φ_v = Shapley of “keep original mechanism”
```

If \(\phi_v\) is near zero, the original mechanism is not earning its cost — flip is cheap to try. If \(\phi_v\) is large and *negative*, the original mechanism is actively hurting quality — flip (or fix) is urgent. If \(\phi_v\) is large and positive, the original mechanism is load-bearing; a flip must preserve that contribution (e.g. FlipToDet only if \(f_v\) matches the mode of \(\pi_v\)).

**Cost warning.** Full Shapley over \(n\) agents is \(2^n\) pipeline re-runs, each live. The FinanceBench case study used 36 coalition evaluations × 5 queries. This is L2. v0 uses leave-one-out + a cheap observational Shapley proxy (Section 8), and spends live Shapley only on the top-k candidates.

### 2.6 WHEN2TOOL and “To Call or Not to Call” — tool necessity

These papers answer a question adjacent to the flip: *should this step invoke a tool at all?* That is the special case FlipToDet of a *tool-calling decision*, or FlipToNondet of “always call / never call.”

#### WHEN2TOOL — arXiv:2605.09252

**Paper:** [Sun et al. *LLM Agents Already Know When to Call Tools — Even Without Reasoning.* arXiv:2605.09252](https://arxiv.org/abs/2605.09252)  
**Code:** [https://github.com/Trustworthy-ML-Lab/when2tool](https://github.com/Trustworthy-ML-Lab/when2tool)  
**Site:** [https://lilywenglab.github.io/when2tool/](https://lilywenglab.github.io/when2tool/)

Benchmark: 18 environments (15 single-hop, 3 multi-hop), three necessity categories, three difficulties, 1,080 train / 2,700 test.

| Category | Self-assessment | Easy vs hard |
|---|---|---|
| A. Computational scale | “Can I compute this?” | \(235\times 48\) vs trillion-scale / \(C(80,40)\) |
| B. Knowledge boundary | “Do I know this?” | Capital of France vs fictional entities |
| C. Execution reliability | “Can I execute this faithfully?” | `print(2+3)` vs 20-iteration DP |

**Findings we rely on:**

1. Models default to over-calling. Prompt-only suppression is indiscriminate; hard tasks lose ~2.5× more accuracy per saved call.
2. Reason-then-Act only partially helps and can collapse tool use on Llama (accuracy 79.5% → 31.2% on Llama-3.1-8B) because the model narrates intent but never emits a valid invocation.
3. Tool necessity is **linearly decodable** from the pre-generation hidden state (last input token) with AUROC **0.89–0.96** across Qwen3 1.7B–32B and Llama-3.1/3.3 — substantially better than verbalized reasoning.
4. **Probe&Prefill:** L2-regularized logistic probe + prefill a steering sentence (`I can solve this directly` / `I need to use a tool`). 48% tool-call reduction at 1.7% accuracy loss; 20–56% API-call reduction on Search-o1. Overhead < 1 ms.

**v0 constraint:** hidden-state probes require **open weights** and a hook into prefill. Hosted Claude / GPT / Gemini expose no hidden states. Retrain probes on every model upgrade; expect distribution-shift drift.

#### To Call or Not to Call — arXiv:2605.00737

**Paper:** [Wu et al. *To Call or Not to Call: A Framework to Assess and Optimize LLM Tool Calling.* arXiv:2605.00737](https://arxiv.org/abs/2605.00737)  
**Code:** [https://github.com/QinyuanWu0710/ToCall_or_NotToCall](https://github.com/QinyuanWu0710/ToCall_or_NotToCall)

Decision-theoretic decomposition (Rational Choice Theory):

| Factor | Normative (true) | Descriptive (perceived) |
|---|---|---|
| **Necessity** \(N^\star(x)\) | No-tool score below quality threshold | Model’s self-report (“do you need help?”) |
| **Utility** \(\Delta^\star(x) = s^{\mathrm{AT}}(x) - s^{\mathrm{NT}}(x)\) | Always-tool minus no-tool | Inferred from whether the model actually called |
| **Affordability** | Call iff expected gain > cost; under budget \(K\), pick the \(K\) largest positive \(\Delta^\star\) | First \(K\) self-decided calls |

Three experimental setups — **No Tool / Always Tool / Self-decision** — are the correct identification strategy for necessity and utility. Utility is upper-bounded by need: if the model already solves \(x\), a call cannot have positive utility. Empirically, calls *hurt* when there is no need (e.g. 32% of high no-tool factuality instances degraded under Always Tool for GPT-OSS-120B). Four of seven models made redundant calls and performed *worse* than a better allocation.

**Latent Need Estimator (LNE)** from hidden states predicts true need better than self-report and improves budgeted allocation. **Latent Utility Estimators (LUE)** do *not* reliably predict true utility — utility estimation remains open. This is load-bearing for us: v0 can estimate *necessity* more confidently than *utility of a flip*.

A sibling paper, [arXiv:2605.18882](#ibh-2026), diagnoses an **Intrinsic Bias Hypothesis**: an activation-independent call offset so the model favors calling even at activation parity. SAE-based Adaptive Margin-Calibrated Steering cancels the offset. Useful if we ever steer rather than refactor.

**Flip mapping:**

- High true necessity + low variance of the *tool output* → the LLM should not be doing the work; FlipToDet the *compute/lookup*, keep a thin LLM only if integration is needed.
- Low true necessity + high self-decision call rate → FlipToDet the *router* to “don’t call” (or Probe&Prefill).
- High true utility of *judgment* that no function captures → do **not** FlipToDet the proposer.
- Negative true utility of a tool → FlipToNondet is the wrong direction; *remove* the tool or degrade it (counterfact).

### 2.7 Related attribution we do not treat as load-bearing

- **Who&When** ([arXiv:2505.00212](#whowhen-2025)): defines the failure-attribution task; SOTA log-only judges ~14% step-level. Reason we refuse correlational LLM-judge attribution as a primary estimator.
- **AgenTracer** ([arXiv:2509.03312](#agentracer-2025)): oracle substitution (replace action with a *gold* action) + trained scorer. Different from same-policy `do_resample`. Gold actions are not a flip.
- **Ma et al.** ([arXiv:2509.08682](#ma-2025)): Shapley + causal discovery over *static* logs. Observational.
- **DoVer** ([arXiv:2512.06749](#dover-2026)): multi-agent, framework-level checkpoint/replay, log-based hypotheses then targeted intervention. Heavier than we want for v0.
- **GraphTracer** ([arXiv:2510.10581](#graphtracer-2025)): graph-guided failure tracing for multi-turn search.

---

## 3. LangGraph time-travel and checkpointers, as they actually work

**Docs:** [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers) · [Use time-travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel) · [Persistence concept](https://github.com/langchain-ai/langgraph/blob/main/docs/docs/concepts/persistence.md)

LangGraph is the most common production graph runtime we will ingest. Its “time travel” is a **checkpoint-restart primitive**, not a VCR. Using it as if it were Tracefork/AgentReplay is the most likely v0 implementation bug.

### 3.1 What a checkpointer actually stores

Compile a graph with a checkpointer (`InMemorySaver`, `PostgresSaver`, …). At each **super-step** boundary LangGraph writes a `StateSnapshot`:

| Field | Meaning |
|---|---|
| `values` | Channel values (graph state) |
| `next` | Nodes scheduled next; `()` means done |
| `config` | `{thread_id, checkpoint_ns, checkpoint_id}` |
| `metadata` | `source` ∈ {`input`,`loop`,`update`}, `writes`, `step` |
| `parent_config` | Previous checkpoint |
| `tasks` | Per-node tasks; subgraph snapshot if `subgraphs=True` |

A **super-step** is one tick: all scheduled nodes run, possibly in parallel. Sequential `START → A → B → END` produces checkpoints after input, after A, after B. You can only resume from a super-step boundary.

Additionally, **pending writes** persist per-node outputs inside a super-step so a sibling failure does not recompute successful nodes. Those writes are *not* full snapshots; time travel still resumes from super-step checkpoints.

**Threads.** `thread_id` is the primary key. Without it, nothing persists.

**Namespaces.** `checkpoint_ns == ""` is the parent graph; `"node:uuid"` is a subgraph; nested subgraphs join with `|`.

### 3.2 Replay vs fork

```python
history = list(graph.get_state_history(config))          # newest first
before = next(s for s in history if s.next == ("node_v",))

# REPLAY — re-executes node_v and everything after. LLM calls fire AGAIN.
graph.invoke(None, before.config)

# FORK — does NOT roll back the thread. Creates a new checkpoint branched
# from `before`, then continues. Original history stays intact.
fork_cfg = graph.update_state(before.config, values={...}, as_node="upstream")
graph.invoke(None, fork_cfg)
```

Official docs are explicit:

> Replay re-executes nodes — it doesn’t just read from cache. LLM calls, API requests, and interrupts fire again and may return different results.

`update_state` applies values through the specified node’s writers (including **reducers**). Infer `as_node` from version history unless: parallel branches (`InvalidUpdateError`), a fresh thread, or you are *skipping* nodes (set `as_node` to a later node so the graph thinks it already ran).

**Interrupts always re-trigger** on time travel. The node containing `interrupt()` re-executes and waits for a new `Command(resume=...)`.

### 3.3 Subgraphs (granularity trap)

- Default: subgraph inherits the parent checkpointer. The parent treats the **entire subgraph as one super-step**. You cannot time-travel *between* subgraph nodes.
- `compile(checkpointer=True)` on the subgraph: per-step checkpoints inside it. Access via `get_state(config, subgraphs=True)` → `tasks[0].state.config`.

If the node you want to flip lives inside a default subgraph, parent-level time travel re-runs the whole subgraph. That silently inflates the intervention.

### 3.4 What this is good for, and what it is not

| Want | LangGraph time-travel | Need instead |
|---|---|---|
| Resume after HITL / crash | Yes — this is the design center | — |
| Fork state and explore a branch *live* | Yes | — |
| $0 bit-exact replay of a production LLM call | **No** | Tracefork tape / AgentReplay cassette |
| Hash-verify that replay matched | **No** | sha256 body check |
| Residual-nondeterminism metric | **No** | CAR action-match rate |
| Flip a node without re-paying the prefix | Partial (prefix not re-executed, but tail is live) | Hybrid cassette |

**v0 composition:** use LangGraph checkpoints as the *graph-shaped index* (which node, which state, which `next`). Use a cassette/tape at the HTTP seam as the *I/O-shaped record*. A flip is: `update_state` to install \(f_v\)’s output (or a sampled \(\pi_v\)), then either (a) cassette-replay the tail if call-sites still match, or (b) live-invoke the tail under a budget.

Tracefork already documents a “tape-backed LangGraph time-travel” adapter: the framework layer supplies step structure; the byte seam stays at httpx. That is the correct integration shape.

---

## 4. What a “scientific” flip simulation requires

Pearl’s ladder ([Pearl 2009](#pearl-2009)):

1. **Association** (rung 1): \(P(y \mid \mathrm{see}(v \text{ looks noisy}))\). Observational. Confounded.
2. **Intervention** (rung 2): \(P(y \mid \mathrm{do}(\delta(v)=\mathrm{DET}))\). What we want.
3. **Counterfactual** (rung 3): \(P(y_x \mid y_{x'})\). “This *same* run, had \(v\) been DET.” Requires a structural model plus an abduction of the exogenous noise \(U\).

L2 policy-swap with \(K\) rollouts estimates rung 2. Rung 3 is harder: the exogenous noise of an LLM is not a seed you can hold fixed once contexts diverge (CAR’s “common random numbers” limitation). **v0 estimates rung 2, never claims rung 3.** UI copy must say “runs like these, under a flip” — not “this exact incident would have gone the other way.”

Identification assumptions for a rung-2 flip:

1. **Faithful state reconstruction.** \(s_k\) is actually the state the node decided from. Missing tool schemas, truncated history, or redacted PII that the model *saw* break this.
2. **No unrecorded side channels.** Clock, RNG, sibling-network calls, prompt-cache effects.
3. **Stable mechanisms elsewhere.** Downstream \(\pi_{w \neq v}\) and tools are the same in factual and counterfactual worlds, except as caused by the flip. A model-version bump between record and replay is a different intervention (`do_policy` on *all* LLM nodes).
4. **SUTVA / no interference.** Flipping \(v\) on this run does not change other users’ batches (it does, on hosted APIs — that is residual nondeterminism).
5. **Outcome function stability.** \(Y\) does not itself flip with the architecture (a judge that prefers “more natural language” will punish FlipToDet).

When any of (1)–(5) fail, we degrade to proxies and widen CIs (Section 8).

---

## 5. Practical approximation strategies (when you cannot re-run the LLM)

This is the v0 center of gravity. Live L2 is the *confirmation* tier, not the default.

### 5.1 Historical variance as a proxy for `do_resample`

**Idea.** `do_resample(k)` estimates \(\mathrm{Var}(a_k \mid s_k)\) and the induced \(\mathrm{Var}(y)\). If we have many production traces, we can estimate a *coarsened* version from history.

**Procedure.**

1. Define an input key \(h(s) = \mathrm{sha256}(\mathrm{canonicalize}(s))\) using AgentReplay-style canonicalization (drop request ids, sort keys, redact timestamps). Optionally coarsen further: schema-only key, embedding cluster, or “tool-name + arg-shape.”
2. For each node \(v\) and each key, collect the multiset of outputs \(\{a^{(i)}\}\) and downstream outcomes \(\{y^{(i)}\}\).
3. Estimate:
   - **Action entropy** \(\hat{H}(A \mid h(S))\) (token-normalized; or exact-match entropy after schema parse).
   - **Mode mass** \(p_{\mathrm{mode}} = \max_a \hat{P}(a \mid h(S))\).
   - **Outcome variance** \(\widehat{\mathrm{Var}}(Y \mid h(S))\).
   - **Wilson CI** on \(p_{\mathrm{mode}}\) and on failure rate.

**Interpretation.** High \(p_{\mathrm{mode}}\) + low \(\hat{H}\) + parseable schema ⇒ the node is *already almost a function*. FlipToDet to “return the mode / run the parser” is a low-regret refactor. Low \(p_{\mathrm{mode}}\) can mean (a) genuine ambiguity that needs an LLM, or (b) a bad key (over-coarsened or under-coarsened). Report both \(n\) and the CI; refuse to recommend on \(n < n_{\min}\) (v0 default \(n_{\min}=30\) per node, or 8 per coarse key).

**This is observational.** Same-input / different-output is *evidence of residual stochasticity*, not a causal effect of flipping. Confounders: model-version mix, prompt drift, time-of-day batch effects, A/B flags. Stratify by `model_id`, `prompt_hash`, `graph_version` or the proxy is junk.

### 5.2 Synthetic deterministic oracle from observed outputs

When we do not have \(f_v\) yet, we *synthesize a candidate* from history and score it offline.

**Majority-vote oracle.** For each key, \(f_{\mathrm{maj}}(s) = \arg\max_a \mathrm{count}(a \mid h(s))\). Ties → `UNDECIDED` (do not flip those keys).

**Schema-check oracle.** If outputs are structured, \(f_{\mathrm{sch}}\) is: parse → validate → fill defaults → reject. This is an SDB verifier promoted to the proposer. Score it by historical accept rate and by whether rejects correlate with downstream failure (if rejects *prevent* bad commits, FlipToDet of the *gate* is independently valuable even when the proposer stays an LLM).

**Program-synthesis oracle (optional, not v0-default).** Use the CausalFlow contrastive pair \((s_i, s_i^\star)\) plus historical \((s, a)\) to propose a small function (regex, SQL, DSL). Accept only if it matches the majority vote on a held-out slice of keys and has no side effects.

**Offline scoring (no new LLM calls):**

\[
\begin{aligned}
\widehat{\Delta}_{\mathrm{fail}} &= \hat{P}(Y_{\mathrm{fail}} \mid a = f(s)) - \hat{P}(Y_{\mathrm{fail}}) \\
\widehat{\Delta}_{\mathrm{var}}  &= 0 - \widehat{\mathrm{Var}}(A \mid h(S)) \quad \text{(DET variance is 0 by construction on decided keys)} \\
\widehat{\Delta}_{\mathrm{cost}} &= c(f) - \bar{c}(\pi_v) \\
\widehat{\Delta}_{\mathrm{lat}}  &= \ell(f) - \bar{\ell}(\pi_v)
\end{aligned}
\]

Coverage \(=\hat{P}(f(s) \neq \mathrm{UNDECIDED})\) is a first-class metric. A function that is perfect on 40% of traffic and `UNDECIDED` on 60% is a *partial* FlipToDet (LLM fallback), not a full replacement. Recommend the hybrid.

### 5.3 Cheap judge models

Use a small judge *only* for outcomes that have no rule. CAR: “Judge-based outcome functions inject their own noise; rule-based outcomes are preferred for anything to be trusted.” CausalFlow’s browsing-repair audit: 86–91% judge precision.

**v0 judge policy:**

- Prefer executable verifiers (tests, schema, policy predicates, exact match).
- If a judge is required, fix the judge model/version, temperature 0, and a rubric with *anchored* examples. Double-judge a 5–10% slice; report agreement. If agreement < 0.8 Cohen’s \(\kappa\), do not use the judge for a flip recommendation.
- Never use a judge as the *attribution* mechanism (Who&When ~14%). Judges score \(Y\); interventions estimate effects.
- Cost: a Haiku/Flash/8B judge on recorded I/O is 1–2 orders of magnitude cheaper than re-rolling the production model through a tail. Still not free — budget it.

### 5.4 Hidden-state probes (WHEN2TOOL / LNE)

When the node is an **open-weights** model we operate:

1. Record the last-token prefill hidden state (or re-prefill offline from the recorded prompt — cheaper than generation).
2. Train LNE / WHEN2TOOL probes on labeled necessity (from No-Tool vs Always-Tool on a cheap slice, or from historical success-without-tool).
3. Use the probe as a **router FlipToDet**: `if p_need < τ: skip tool / skip LLM-planner; else keep`. Sweep \(\tau\) for a Pareto curve (WHEN2TOOL’s actual contribution).

When the node is hosted: skip probes. Fall back to the descriptive/normative setups of Wu et al. on a *sampled* cheap slice (No Tool / Always Tool / Self-decision with a small model as a stand-in — label this as a **surrogate**, not a measurement of the hosted model).

### 5.5 Offline replay of recorded I/O only (L0)

This is Tracefork replay + AgentReplay REPLAY + cassette mutate:

1. Reconstruct \(G\) and align steps to nodes.
2. For FlipToDet: `mutate` the node’s recorded completion to \(f_v(s)\) (majority vote, schema fill, or a user-supplied function).
3. Replay. Two outcomes:
   - **Cassette hit all the way.** Downstream call-sites still match. You have a *bound*: the flip did not change what the agent asked next, so L0 ≈ L1. Report “tail-stable.”
   - **First miss at step \(j\).** The flip changed downstream inputs. L0 *cannot* continue honestly. Stop. Report “diverges at \(j\); L0 estimate is prefix-only.” Optionally queue for L1 hybrid under budget.

**Hash-verify every served body.** If you cannot hash-verify, you do not have L0; you have a log viewer.

### 5.6 Approximation ladder (use in this order)

```
L0 tape splice + historical variance + majority/schema oracle
        ↓  if candidate survives and tail is unstable
L1 hybrid fork (live tail, budget-capped)
        ↓  if recommendation would ship to production
L2 policy-swap K-rollout (CAR do_policy) on a held-out slice
        ↓  always
Shadow / canary in production (the only estimator that is not a simulation)
```

Each level’s output is an input prior to the next, not a replacement for it.

---

## 6. Reconstructing the architecture graph from traces

v0 ingestion, in order of fidelity:

1. **Native graph** (LangGraph `StateGraph`, CrewAI crew, OpenAI Agents handoffs). Nodes and edges are declared. Best.
2. **Typed trace** (CausalFlow `StepType`, OpenTelemetry `gen_ai.*`, OpenInference). Recover nodes by `name` / `step_type`; edges by dependency indices or parent-span ids.
3. **HTTP-seam tape** (Tracefork / AgentReplay). Nodes are call-sites; edges are happens-before in the event log. Infer TOOL vs LLM from URL / SDK. Weaker on intra-process functions (no HTTP).
4. **Log scrape** (`counterfact discover`). Last resort. Mark graph quality = LOW; refuse high-confidence recommendations.

**Ambiguous steps** (the ones we score) are nodes where \(\delta(v)\) is STOCH *and* the output is schema-like, or DET *and* the failure cluster looks like “needed judgment.” Heuristics for the candidate set:

- LLM node whose outputs parse as JSON / enum / SQL / tool-args on ≥ 80% of traces.
- LLM node with \(p_{\mathrm{mode}} \ge 0.7\) on its top keys.
- LLM node that is the CAR point-of-commitment for policy violations.
- DET node with a heavy tail of `UNHANDLED` / default-branch / parse failures.
- Tool-calling LLM with WHEN2TOOL-style over-call (high call rate on historically solvable-without-tool keys).

---

## 7. Recommended v0 methodology

**Design goals, in order:** (1) do not lie, (2) cost ≈ replay + a cheap judge, (3) still produce a refactor a staff engineer would try on a canary.

### 7.1 What v0 will not do

- Will not claim bit-exact hosted-LLM replay.
- Will not treat LangGraph `invoke(checkpoint)` as a flip simulation.
- Will not use an LLM judge as the *cause* of a recommendation.
- Will not run full Shapley over live coalitions by default.
- Will not claim “this incident would have succeeded.”
- Will not recommend a flip on \(n < n_{\min}\) or on a LOW-quality graph without a loud warning.

### 7.2 v0 algorithm

```
algorithm DeterminismAdvisorV0(traces, G=None, budget_usd=0.0):
    # --- A. Ingest -------------------------------------------------------
    G ← G or ReconstructGraph(traces)          # §6
    tape ← BuildContentAddressedTape(traces)   # Tracefork / AgentReplay
    fidelity ← HashVerifyReplay(tape)          # must pass or abort
    report residual_nondeterminism:
        action_match_rate if any live LLM replay was attempted
        else "L0-only; LLM match rate not measured"

    # --- B. Type and candidate ------------------------------------------
    for v in G.nodes:
        type_v ← CausalFlowStepType(v)         # or post-hoc classify
        stats_v ← HistoricalStats(v, traces)   # §5.1
            # n, p_mode, H, schema_ok, cost, lat, fail, policy_viol
            # stratified by model_id, prompt_hash, graph_version
        candidates ← Ambiguous(v, stats_v)     # §6 heuristics

    # --- C. Synthesize oracles (no LLM) ---------------------------------
    for v in candidates:
        f_maj  ← MajorityVoteOracle(v, traces)      # §5.2
        f_sch  ← SchemaOracle(v)                    # may be None
        f_user ← UserSuppliedFunction(v)            # optional
        f_v    ← first of {f_user, f_sch, f_maj} that coverage ≥ γ
                  else Hybrid(f_*, LLM_fallback)

    # --- D. L0 splice ----------------------------------------------------
    for v in candidates:
        for τ in Sample(traces, v, m=min(50, n_v)):
            τ' ← MutateCassette(τ, v, f_v(s))       # AgentReplay mutate
            r  ← ReplayStrict(τ')                   # hash-checked
            if r.miss:
                mark DIVERGENT(v, τ, at=r.j)
            else:
                record L0_delta(v, τ, Y(τ')-Y(τ))   # cost/lat/fail/var/...

        # Observational deltas even when divergent:
        record OBS_delta(v) from stats_v vs f_v on matching keys

    # --- E. Optional cheap judge on recorded I/O -------------------------
    if need_soft_quality:
        judge ← FixedSmallJudge()
        κ ← AgreementOnSlice(judge, gold_or_double, 0.1)
        if κ < 0.8: disable judge; else score Y_quality on L0 pairs

    # --- F. Optional L1 under budget ------------------------------------
    spend ← 0
    for v in RankByExpectedValue(candidates):      # §12 score
        if spend ≥ budget_usd: break
        if DIVERGENT_rate(v) == 0 and CI_excludes_zero(OBS+L0):
            continue                                # L0 enough
        for τ in TopDivergent(v, k=5):
            tail ← HybridFork(τ, v, f_v)            # live tail
            spend += tail.usd
            record L1_delta(v, τ, Y(tail)-Y(τ))

    # --- G. Optional tool-necessity (open weights only) ------------------
    if open_weights(v):
        probe ← FitLNE(hidden_states or re_prefill(prompts))
        record necessity_auroc, pareto_curve(τ)

    # --- H. Decision -----------------------------------------------------
    for v in candidates:
        rec_v ← Decide(v, OBS, L0, L1, probe)       # §12
        rec_v.ci ← Wilson_or_bootstrap(...)
        rec_v.caveats ← ValidityThreats(v)          # §9
        rec_v.level ← {L0, L1, L2_not_run}

    return Report(G, recs, fidelity, spend,
                  banner="Simulation ≠ production. Canary required.")
```

### 7.3 Estimators v0 actually ships

| Estimator | Rung | Default on? | CI |
|---|---|---|---|
| Historical \(p_{\mathrm{mode}}\), entropy, fail rate | 1 | Yes | Wilson |
| Majority / schema oracle coverage + match | 1 | Yes | Wilson |
| L0 cassette splice, tail-stable subset | 2-partial | Yes | Bootstrap on paired deltas |
| L0 divergence rate (where splice cannot continue) | diagnostic | Yes | Wilson |
| Cheap judge on recorded I/O | 1 (noisy \(Y\)) | Opt-in | Cohen’s \(\kappa\) gate |
| L1 hybrid fork | 2 | Budgeted | Bootstrap; small \(n\) |
| WHEN2TOOL / LNE probe | 1 (internal) | Open-weights only | AUROC on held-out |
| CAR `do_resample` / `do_policy` L2 | 2 | Off | Wilson + bootstrap |
| Full Shapley coalitions | 2 | Off | Normal approx; no \(v(S)\) cache |
| CausalFlow CRS | 2 | Off (needs proposals + executor) | Treat as 0/1, not a probability |

### 7.4 Planted-truth gate (non-optional)

Before any customer-facing number:

1. **Synthetic SCM** (CAR): three-step chain, middle step pivotal; AND-failure of two steps. Recover locus and Shapley within tolerance.
2. **Injected-fault tapes** (Tracefork `validate` / `bench`): corrupted tool output, wrong system prompt, poisoned argument, plus a negative control that must *not* be blamed.
3. **Determinism-flip fixtures (ours):** a node that is a majority-vote-able extractor; a node that is open-ended generation. The advisor must recommend DET on the first and NONDET (or ABSTAIN) on the second.

If (1)–(3) fail, we do not ship the estimator. This is the same stance as CAR Phase 0–3 and Tracefork’s “held to ground truth.”

---

## 8. Metrics that matter

Every recommendation carries a vector \(\Delta = \hat{\mathbb{E}}[Y \mid \mathrm{flip}] - \hat{\mathbb{E}}[Y]\), with CIs, plus diagnostics that are *not* outcomes.

### 8.1 Outcome metrics (\(Y\))

| Metric | Definition | How v0 measures | Notes |
|---|---|---|---|
| **Cost** | USD (model + tools + judge) per run | Recorded token/tool bills; \(c(f)\approx 0\) for in-process functions | Do not hide judge/L1 spend |
| **Latency** | End-to-end wall time; also p50/p95 of the flipped node | Trace timestamps; \(f_v\) latency from a microbench | FlipToDet usually wins p95 more than p50 |
| **Failure rate** | \(P(\mathcal{V}=0)\) for a *declared* verifier | Schema, tests, policy predicates, exact match; judge only if gated | Define \(\mathcal{V}\) *before* looking at \(\Delta\) |
| **Output variance** | Action entropy; embedding dispersion; exact-match disagreement across resamples or historical keys | Historical \(\hat{H}\); L0 variance is 0 on decided keys | Variance collapse can be good (audit) or bad (lost coverage) |
| **Auditability** | Fraction of commits with a replayable, hash-verifiable, policy-explained trail | Tape digest present? Verifier reason codes? | FlipToDet of a gate raises this even if accuracy is flat |
| **Policy compliance** | \(P(\mathrm{commit\ violates\ policy})\) | Deterministic predicates on tool args + state ([arXiv:2607.07405](#gates-2026)) | This metric should be *exactly* 0 after a correct gate flip; if it is not, the predicate is wrong |

### 8.2 Diagnostic metrics (not \(Y\))

| Metric | Why |
|---|---|
| `action_match_rate` | Residual nondeterminism of any live replay ([CAR](#car-2026), [Thinking Machines](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)) |
| `tape_verify_ok` | L0 integrity (Tracefork) |
| `coverage(f_v)` | Share of keys the oracle decides |
| `divergent_tail_rate` | Share of splices that cannot finish at L0 |
| `n`, `n_stratified` | Sample size after stratification |
| `graph_quality` | NATIVE / TYPED / TAPE / SCRAPE |
| `judge_κ` | If a judge was used |
| `necessity_auroc` | If a probe was fit |
| `crs` / `φ_v` | If L2 / Shapley was run |
| `point_of_commitment` | If CAR contrastive was run — flip *this* node |

### 8.3 Interval convention

- Binary rates: **Wilson score** 95% CI (Tracefork, CAR).
- Paired deltas: **bootstrap** percentile CI on \(\frac{1}{m}\sum_i (Y_i' - Y_i)\).
- Shapley: normal approximation on MC marginals; **no coalition-value cache**.
- **Abstain** if the CI for the *primary* metric (usually failure or policy) includes 0 *and* coverage is incomplete, unless auditability/cost alone justify a hybrid gate (call that out as a *gate* recommendation, not a proposer replacement).

---

## 9. Threats to validity

Named so the report can attach them per recommendation.

### 9.1 Confounding (rung-1 estimators)

Historical variance mixes mechanism noise with **prompt drift, model-version mix, traffic mix, and batch-size-dependent kernels**. Two traces with the same `h(s)` may not be the same \(s\) (canonicalization over-stripped a load-bearing field) or may not share \(\pi\) (silent prompt edit). **Mitigation:** stratify; refuse cross-version pooling; show a version-break chart.

### 9.2 Selection and collider bias

We study *production* traces: they are conditioned on whatever the current architecture already filters. A FlipToNondet that would attract new traffic (more intents handled) is invisible. A FlipToDet that would *reject* traffic the LLM currently “succeeds” at by hallucinating will look like a failure-rate *increase* under \(Y=\) “user accepted the answer,” and a compliance *increase* under \(Y=\) “policy.” **Mitigation:** never optimize a single \(Y\); show the vector.

### 9.3 Distribution shift after refactor (the big one)

The architectural counterfactual changes the *input distribution to downstream nodes*. L0 tail-stable splices systematically **understate** this. L1/L2 on historical prompts still miss:

- Users who adapt to a more rigid system (or abandon it).
- Attackers who adapt to a deterministic gate (or are newly blocked — good).
- Prompt-cache and batching changes that alter residual nondeterminism of *other* LLM nodes.

**Mitigation:** label every pre-production number `historical_mixture`. Require a canary with the same \(Y\) vector. This is not optional for a “ship it” recommendation.

### 9.4 Simulation ≠ production

| Simulation lie | Why it happens | What we do |
|---|---|---|
| Cassette hit ⇒ production hit | Tools are live and stateful; clocks move; inventories change | Sandbox tools or mark `env_stale` |
| Predictive re-execution (CausalFlow) | The predictor is another model | Prefer executors; else widen CI |
| Judge \(Y\) | 86–91% precision in CausalFlow’s audit | \(\kappa\) gate; prefer predicates |
| Seeded local replay | Hosted production is not seeded | Do not transfer local match rates to hosted |
| LangGraph replay | Re-samples the LLM | Do not call it replay |
| Ablation collapse | Retriever removed ⇒ pipeline dies | Degrade or substitute, don’t ablate |
| Gold-action substitution (AgenTracer) | Gold is not a shippable \(f_v\) | Only use gold as an *upper bound* on FlipToDet value |

### 9.5 Interference and residual nondeterminism

Hosted `do_policy` rollouts are not i.i.d.: they share batching, caches, and rate limits. CIs that assume independence are optimistic. **Mitigation:** over-disperse (treat effective \(n\) as smaller); prefer local seeded models for L2 confirmation; report `action_match_rate`.

### 9.6 Side effects and ethics of replay

Re-issuing `issue_refund` or sending email on a counterfactual tail is not a simulation, it is production. CAR scopes real side-effecting tools out unless mocked. **v0: refuse L1/L2 on nodes with `side_effects=mutating` unless a sandbox / dry-run flag is proven.** L0 cassette replay is safe *if and only if* interceptors cover the mutating path.

### 9.7 Goodharting the advisor

If teams optimize to “get a DET recommendation,” they will over-schema outputs and hide variance in unconstrained text fields. **Mitigation:** score unconstrained text separately; do not let a JSON wrapper around a free-form essay count as low entropy.

### 9.8 External validity of planted tests

Tracefork and CAR validate on fixtures. Passing `validate` means the *instrument* is causally responsive, not that customer graphs are simple. **Mitigation:** never quote fixture top-1 as a product accuracy.

---

## 10. Decision criteria: when to recommend DET vs NONDET

A recommendation is one of:

`FLIP_TO_DET` · `FLIP_TO_DET_HYBRID` (function + LLM fallback) · `FLIP_TO_NONDET` · `STRENGTHEN_SDB` (keep proposer, add/harden verifier+commit+reject) · `ABSTAIN`

### 10.1 FlipToDet (LLM/subagent → function/tool)

Recommend when **all** of the following hold, or when (P) holds and we explicitly say “gate, not proposer”:

| ID | Criterion | Default threshold (v0, tunable) |
|---|---|---|
| D1 | Output is schema-shaped | `schema_ok ≥ 0.80` |
| D2 | Historical mode is stable | \(p_{\mathrm{mode}} \ge 0.70\) on keys with \(n_k \ge 8\), or majority-oracle coverage \(\ge 0.60\) at match \(\ge 0.90\) |
| D3 | Primary bad \(Y\) does not worsen on L0 tail-stable set | \(\Delta_{\mathrm{fail}}\) CI upper bound \(\le +0.02\) (2pp) |
| D4 | Cost or latency or variance or compliance improves | At least one of \(\Delta_{\mathrm{cost}}, \Delta_{\mathrm{lat}}, \Delta_{\mathrm{var}}, \Delta_{\mathrm{policy}}\) CI excludes 0 in the beneficial direction |
| D5 | Point of commitment (if known) is this node, not a descendant | CAR locus = \(v\), or unknown |
| D6 | Graph quality is not SCRAPE, or warning accepted | NATIVE / TYPED / TAPE |
| D7 | Sample size | \(n \ge 30\) after stratification |

**Hard DET (override D1–D4):** node is a **policy / commit / spend / PII / auth** gate. Recommend `STRENGTHEN_SDB` or `FLIP_TO_DET` of the *gate* regardless of accuracy. Safety floors are not A/B tests ([SDB](#sdb-2026), [PolicyLayer](https://policylayer.com/blog/deterministic-ai-agent-policies), [arXiv:2607.07405](#gates-2026)).

**Hybrid (most common honest win):** D2 holds on a *subset* of keys. Recommend `FLIP_TO_DET_HYBRID` with coverage and an LLM fallback on `UNDECIDED`. WHEN2TOOL Probe&Prefill is a hybrid router, not a full FlipToDet.

**Do not FlipToDet the proposer when:**

- Outputs are open-ended and variance is *semantic* (different good answers), not schema noise.
- True utility of judgment is positive and no \(f_v\) has coverage (Wu et al.: LUE is weak — if we cannot even *estimate* utility, we do not replace the mechanism).
- The node is a CausalFlow retrieval-gap (local function cannot create missing evidence).
- L0 divergent-tail rate is high **and** we did not run L1 — we do not know the architectural effect.

### 10.2 FlipToNondet (function/tool → LLM/subagent)

Recommend when:

| ID | Criterion |
|---|---|
| N1 | DET node has a heavy unhandled / parse-fail / default-branch tail that correlates with \(Y_{\mathrm{fail}}\) |
| N2 | CausalFlow-style proposals that *add* judgment flip those failures (CRS=1) **or** L1 hybrid with a small LLM on the failing slice improves \(Y\) |
| N3 | The function’s contract is known to be incomplete (new intents, messy text, multi-hop synthesis) |
| N4 | We can wrap the new LLM in an SDB (verifier + commit + reject). **Bare FlipToNondet of a commit path is forbidden.** |
| N5 | Cost/latency regression is accepted and quantified |

**Do not FlipToNondet** a working deterministic policy gate, calculator, or schema validator because an LLM “might be more flexible.” That is how you buy variance and compliance failures. If the function is wrong, *fix the function*.

### 10.3 STRENGTHEN_SDB (often the right answer instead of a flip)

When the proposer must stay stochastic (novel inputs) but failures are at the boundary: add a deterministic verifier, make commit conditional, return typed rejects. This is the 81% “documented fix” pattern in the SDB paper’s post-mortem set. Score it as a first-class recommendation, not a consolation prize.

### 10.4 Decision score (for ranking, not for shipping)

A scalar is useful for sorting candidates, dangerous as a ship bit.

\[
\mathrm{Score}(v) =
w_c(-\Delta_{\mathrm{cost}}) + w_\ell(-\Delta_{\mathrm{lat}}) + w_f(-\Delta_{\mathrm{fail}})
+ w_v(-\Delta_{\mathrm{var}}) + w_a(\Delta_{\mathrm{audit}}) + w_p(-\Delta_{\mathrm{policy}})
\]

v0 default weights: \(w_p = w_f = 3,\ w_c = w_\ell = 1,\ w_v = 1,\ w_a = 2\), then **hard-gate** on Section 10.1–10.3. Weights are product-specific; compliance-heavy deployments should raise \(w_p\) further. Never hide the vector behind the scalar in the UI.

---

## 11. Worked micro-example (illustrative, not a claim)

Support agent, four nodes: `retrieve_order` (DET) → `decide_resolution` (LLM) → `issue_refund` (TOOL) → `draft_reply` (LLM).

Traces: 200 runs, 18 unjustified refunds. Historical stats on `decide_resolution`: outputs are an enum `{REFUND, REPLACE, REJECT, ESCALATE}`; \(p_{\mathrm{mode}}=0.81\) given `(policy_hash, order_status, $amount_bucket)`; schema_ok = 0.96. Majority oracle coverage 0.74 at 0.93 match. Policy predicate `amount ≤ 50 ∧ status=delivered ∧ not_injection` is already written in the prompt and violated 18 times.

L0 splice: replace `decide_resolution` completion with `f_policy(state)` (the predicate + enum). 148/200 cassettes tail-stable (downstream `issue_refund` args still match). On that slice, unjustified refunds 18→0; justified refunds 40→40; cost −$0.004/run (one fewer LLM); `draft_reply` still LLM. 52/200 diverge (agent would have asked a clarifying question). L1 not run (mutating tool).

**Recommendation:** `FLIP_TO_DET` of `decide_resolution` **as a gate** (`STRENGTHEN_SDB` + function), keep `draft_reply` stochastic. Do **not** flip `issue_refund` (commitment is upstream — CAR category error). Banner: L0 tail-stable on 74%; mutating tool blocked L1; canary required; injection cases in the 52 need a red-team slice.

This is the shape of a v0 report.

---

## 12. Implementation notes (so the methodology is implementable)

**Tape / cassette.** Prefer an existing substrate rather than inventing a fourth: AgentReplay (framework adapters, mutate, CI) or Tracefork (hash-chain, Wilson blame, planted validate). Ingest OTel/OpenInference when that is all the customer has; mark graph_quality=TAPE/SCRAPE accordingly.

**LangGraph.** Read checkpoints for node identity and state; do not use `invoke(checkpoint)` as L0. Optional: Tracefork’s tape-backed adapter.

**Outcome functions.** Ship a library of *rule* \(Y\)s: JSON schema, policy DSL, exact match, regex, HTTP status, “tool X not called.” Judges are opt-in.

**Side effects.** `side_effects` taxonomy: `none | read | sandbox_ok | mutating`. L1/L2 allowed on the first three only.

**Privacy.** Tapes contain prompts. Redact at record time; Tracefork’s content redaction is forensic-only (breaks bit-exactness) — say so.

**Versioning.** Every report records `advisor_version`, estimator set, judge id, tape digest, graph digest. Recommendations are not comparable across advisor versions without that.

---

## 13. Explicit limitations (read this before citing v0 numbers)

1. **v0 estimates associations and partial interventions.** Full architectural `do_policy` is off by default.
2. **Hosted LLMs are not deterministic.** Temperature 0 is not a seed ([Thinking Machines Lab 2025](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)).
3. **L0 tail-stable estimates ignore distribution shift** of downstream inputs and of future users.
4. **No hidden-state probes on hosted models.**
5. **Utility of a flip is harder than necessity** ([Wu et al. 2026](#tocall-2026): LUEs fail). We will over-abstain on FlipToNondet.
6. **CRS is a max-indicator**, not a probability; 0 ≠ innocence.
7. **Shapley without live coalitions is a proxy**; live Shapley is expensive and still historical-mixture.
8. **Planted-fixture accuracy is not product accuracy.**
9. **Side-effecting tails are not simulated** unless sandboxed.
10. **Simulation ≠ production.** The only confirmatory estimator is a canary with the same \(Y\) vector.

---

## 14. What “good” looks like for v0 (acceptance)

A staff engineer can:

1. Drop a folder of traces (or a LangGraph thread + cassette).
2. Get a graph picture with node types and candidate highlights.
3. For each candidate, see the \(Y\) vector with CIs, coverage, divergence rate, and a recommendation in the enum above.
4. Click through to the L0 splice that *justifies* the number (hash-verified).
5. See the banner and the attached threats from Section 9.
6. Run `advisor validate` on planted fixtures in CI ($0, offline).

If we cannot do (4) and (6), we do not have a scientific instrument. We have a dashboard.

---

## References

### Core interventional / replay systems

<a id="car-2026"></a>Shah, J. (2026). *Causal Agent Replay: Counterfactual Attribution for LLM-Agent Failures.* arXiv:2606.08275. https://arxiv.org/abs/2606.08275 · https://github.com/jaineet17/causal-agent-replay

<a id="causalflow-2026"></a>Bonagiri, A., Borkar, D., Janno, G., Anderias, et al. (2026). *CausalFlow: Causal Attribution and Counterfactual Repair for LLM Agent Failures.* arXiv:2605.25338. https://arxiv.org/abs/2605.25338

Tracefork. https://github.com/pratik916/tracefork · https://pypi.org/project/tracefork/

AgentReplay. https://github.com/gadda00/agentreplay · https://victorndunda.com/blog/articles/agentreplay-deterministic-replay.html

counterfact. https://github.com/counterfact-labs/counterfact

### Tool necessity

<a id="when2tool-2026"></a>Sun, C.-E., Liu, L., Yan, G., Wang, Z., & Weng, T.-W. (2026). *LLM Agents Already Know When to Call Tools — Even Without Reasoning.* arXiv:2605.09252. https://arxiv.org/abs/2605.09252 · https://github.com/Trustworthy-ML-Lab/when2tool · https://lilywenglab.github.io/when2tool/

<a id="tocall-2026"></a>Wu, Q., Lee, S., Das, S., Amani, M., Nag, A., Gummadi, K., Ravichander, A., & Zafar, M. B. (2026). *To Call or Not to Call: A Framework to Assess and Optimize LLM Tool Calling.* arXiv:2605.00737. https://arxiv.org/abs/2605.00737 · https://github.com/QinyuanWu0710/ToCall_or_NotToCall

<a id="ibh-2026"></a>*To Call or Not to Call: Diagnosing Intrinsic Over-Calling Bias in LLM Agents.* arXiv:2605.18882. https://arxiv.org/abs/2605.18882 · https://github.com/SKURA502/agent-sae/

Model-adaptive tool necessity / knowing–doing gap. arXiv:2605.14038. https://arxiv.org/abs/2605.14038

### Architecture, SDB, gates

<a id="sdb-2026"></a>*A Methodology for Selecting and Composing Runtime Architecture Patterns for Production LLM Agents.* arXiv:2605.20173. https://arxiv.org/abs/2605.20173 · https://www.agentpatternscatalog.org/patterns/stochastic-deterministic-boundary/

<a id="gates-2026"></a>*Deterministic Gates for Reliable LLM Agents.* arXiv:2607.07405. https://arxiv.org/abs/2607.07405

PolicyLayer. *Why AI Agent Policies Must Be Deterministic, Not Probabilistic.* https://policylayer.com/blog/deterministic-ai-agent-policies

### Attribution benchmarks and adjacent methods

<a id="whowhen-2025"></a>Zhang, S., et al. (2025). *Which Agent Causes Task Failures and When? On Automated Failure Attribution of LLM Multi-Agent Systems.* ICML 2025. arXiv:2505.00212.

<a id="agentracer-2025"></a>AgenTracer (2025). *Annotating Failed Multi-Agent Trajectories via Counterfactual Replay.* arXiv:2509.03312.

<a id="ma-2025"></a>Ma, Y., et al. (2025). *Automatic Failure Attribution and Critical Step Prediction via Causal Inference.* arXiv:2509.08682.

<a id="dover-2026"></a>Ma, M., et al. (2026). *DoVer: Intervention-Driven Auto Debugging for LLM Multi-Agent Systems.* arXiv:2512.06749.

<a id="graphtracer-2025"></a>Zhang, H., et al. (2025). *GraphTracer: Graph-Guided Failure Tracing in LLM Agents.* arXiv:2510.10581.

Cemri, M., et al. (2025). *Why Do Multi-Agent LLM Systems Fail?* (MAST). arXiv:2503.13657.

### Causal foundations

<a id="pearl-2009"></a>Pearl, J. (2009). *Causality: Models, Reasoning, and Inference* (2nd ed.). Cambridge University Press.

Halpern, J. Y., & Pearl, J. (2005). Causes and explanations: A structural-model approach. Part I: Causes. *British Journal for the Philosophy of Science, 56*(4), 843–887.

<a id="everitt-2021"></a>Everitt, T., Carey, R., Langlois, E., Ortega, P. A., & Legg, S. (2021). *Agent Incentives: A Causal Perspective.* AAAI. arXiv:2102.01685.

<a id="kenton-2023"></a>Kenton, Z., et al. (2023). *Discovering Agents.* *Artificial Intelligence, 322.* arXiv:2208.08345.

Mesnard, T., et al. (2021). *Counterfactual Credit Assignment in Model-Free Reinforcement Learning.* ICML. arXiv:2011.09464.

Foerster, J., et al. (2018). *Counterfactual Multi-Agent Policy Gradients (COMA).* AAAI.

Castro, J., Gómez, D., & Tejada, J. (2009). Polynomial calculation of the Shapley value based on sampling. *Computers & Operations Research, 36*(5), 1726–1730.

### Record/replay and inference determinism

O’Callahan, R., et al. (2017). *Engineering Record and Replay for Deployability* (Mozilla `rr`). USENIX ATC.

Thinking Machines Lab (2025). *Defeating Nondeterminism in LLM Inference.* https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ · https://github.com/thinking-machines-lab/batch_invariant_ops

VCR.py. https://github.com/vcrpy/vcrpy

Rewind. https://github.com/llm-rewind/rewind

### LangGraph

LangGraph checkpointers. https://docs.langchain.com/oss/python/langgraph/checkpointers

LangGraph time-travel. https://docs.langchain.com/oss/python/langgraph/use-time-travel

LangGraph persistence (source docs). https://github.com/langchain-ai/langgraph/blob/main/docs/docs/concepts/persistence.md

---

## Document history

| Version | Notes |
|---|---|
| 0.1 | Initial methodology: CAR / CausalFlow / Tracefork / AgentReplay / counterfact / WHEN2TOOL / To Call / LangGraph; L0–L2 ladder; v0 algorithm; DET/NONDET criteria; threats. |
