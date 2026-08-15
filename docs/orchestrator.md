# Orchestrator

**Dated 2026-08-15.** The control-flow owner is a **graph-level** object, not a leftover `workflow` span. Doctrine: [agent-architectures.md](agent-architectures.md). Node lattice: [type-lattice.md](type-lattice.md).

**Simulation ≠ production.** Orchestrator actions are observational L0. A canary with the same outcome vector is confirmatory.

## What it is

The orchestrator owns: step budget, who speaks next, HITL gates. Anthropic’s orchestrator–workers is the named form. Production aliases: supervisor, brain, parent, triage, kickoff. Same job.

Repo skill: orchestrator sits above policy, context, model, and tools ([agentic-system-design](../.cursor/skills/agentic-system-design/SKILL.md)).

We do **not** claim “nobody does multi-agent orchestration.” LangGraph supervisor, CrewAI, MAF, and the OpenAI Agents SDK already do. We recommend *re-typing or bounding the hub on an ingested graph*.

## Identification

Pick **at most one** hub per trace family. Infer from existing spans only.

| Signal | Hub kind |
|---|---|
| Root `invoke_workflow` (CrewAI kickoff already mapped here) | `code_workflow` if the path is a code envelope; else `llm_supervisor` if a model chose workers |
| Parent `invoke_agent` / supervisor-named node (not nested under another agent) | `llm_supervisor` |
| LangGraph checkpoint ns parent | same as parent agent |
| Several competing roots | **ABSTAIN** on the orchestrator block; still recommend leaf flips |
| No envelope | **ABSTAIN** |

Advisor-owned labels: `advisor.orchestrator.id`, `advisor.orchestrator.kind` ∈ {`code_workflow`, `llm_supervisor`, `unknown`}.

**Never invent** `gen_ai.orchestrator.*` or `gen_ai.agent.handoff.*`.

## Metrics (observational)

| Metric | Meaning | If missing |
|---|---|---|
| `hops` | Mean hub visits per trace | ABSTAIN on bound |
| `fan_out` | Distinct workers / tools under the hub | — |
| `revisit_rate` | Same worker chosen again with no progress | — |
| `p_next` / Wilson | Stability of next-hop after a hub visit | ABSTAIN on code-route |
| `token_share` | Hub tokens / total tokens | omit; do not guess |
| `has_step_bound` | Only if traces show a consistent hard stop | omit; **do not** infer from prompts |
| `hits_sensitive_ungated` | Hub → refund/commit/auth/PII with no intervening DET gate | false if not observed |

`n_min` and Wilson still apply. Estimator label: `observational_l0_proxy`.

## Actions (report-level)

| Action | When |
|---|---|
| `BoundOrchestrator` | Mean hops high or `revisit_rate ≥ 0.30` (unbounded loop / no progress key) |
| `StrengthenOrchestrator` | `hits_sensitive_ungated` — keep the hub; add HITL / policy gate; do not FlipToNondet the hub |
| `FlipOrchestratorToCode` | `llm_supervisor` and next-hop `p_next` + Wilson ≥ `0.70` — replace with a code router / DAG |
| `CollapseOrchestrator` | `fan_out ≥ 2`, path shape stable (`p_path` + Wilson ≥ `0.70`), no isolation win — drop to one agent + tools or a fixed workflow |
| `ABSTAIN` | No single hub, `n < n_min`, or no rule’s CI excludes the threshold |

Priority: ungated sensitive → `StrengthenOrchestrator`; then bound; then code-route; then collapse; else ABSTAIN.

## Failure modes we look for

- **Hub fragility** — hop count and hub tokens grow with workers, not with task size
- **Missing bound** — long tails of revisit-the-same-worker
- **LLM-as-router** — next-worker is schema-stable but still a chat
- **Over-orchestration** — supervisor + N workers on a path a single tool-using agent already completes
- **Ungated sensitive** — hub reaches refund/commit/auth with no DET gate
- **Handoff loops** — A→B→A with no progress key

## What we will not do

- Guess `has_step_bound` from system prompts
- Auto-tune the hub’s model id or prompt
- Emit `SwapModel` / `FlipToRAG`
- Auto-apply a supervisor rewrite
- Treat MAF traces as LangGraph (P2 refuse-with-reason still holds)
