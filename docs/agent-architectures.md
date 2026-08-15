# Agent architectures

**Dated 2026-08-15.** Doctrine for Superdeterminism’s Architecture Advisor. Not a claim that we invented these patterns.

**Simulation ≠ production.** This file says when a *role* flip is *doctrinally* legal. Evidence and ABSTAIN live in [methodology.md](methodology.md) and [type-lattice.md](type-lattice.md). Orchestrator-specific tracking is [orchestrator.md](orchestrator.md).

Do **not** invent Agent Patterns Catalog IDs. The catalog MCP was not queried for this document.

## The load-bearing split

Anthropic’s [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (19 Dec 2024; still the cited doctrine in 2026):

- **Workflow** — LLMs and tools on *predefined code paths*. You own the control flow.
- **Agent** — the LLM *dynamically* directs process and tool use. You own the goal and the guardrails.

Both are *agentic systems*. A workflow is not “less advanced.” It is cheaper, more auditable, and usually enough.

Repo skill [agentic-system-design](../.cursor/skills/agentic-system-design/SKILL.md) encodes the same stack: orchestrator (step budget, branching, HITL) → policy → context → model → tools.

## Escalation ladder

Use the **lowest** rung that the traces support. Do not climb because a framework makes it easy.

| Rung | Who owns the path | Use when |
|---|---|---|
| 1. Augmented LLM | Prompt + retrieval + tools | One-shot classify / extract / draft |
| 2. Prompt chaining | Fixed sequence + programmatic gates | Decomposable steps (outline → write → check) |
| 3. Routing | Classifier or code edge → specialist | Distinct categories, different prompts/models |
| 4. Parallelization | Code fan-out (sectioning or voting) | Independent aspects or confidence votes |
| 5. Orchestrator–workers | Central hub delegates *unpredictable* subtasks | Subtasks cannot be enumerated in advance |
| 6. Evaluator–optimizer | Generate / critique loop with a rubric | Iterative refinement measurably helps |
| 7. Autonomous agent | ReAct-style loop, model chooses tools | Path cannot be hardcoded; environment gives ground truth |

Climb only when a lower rung’s failure cluster is visible on the tape. Eval platforms score the current rung; they do not recommend a rung change. That is our job — on an *ingested* graph, not a search space.

## Multi-agent topologies (not interchangeable)

| Topology | Control | Return | 2026 default? |
|---|---|---|---|
| **Sub-agent** | Parent dispatches | Child returns one structured result; child context dies | Yes, when isolation is proven |
| **Supervisor** | Hub keeps the global thread | Workers return; hub decides next | Yes, when a global view is required |
| **Handoff / swarm** | Peer transfer | No return to a hub | No. Hard to debug; not the production default |

Pick one. Do not mix supervisor and swarm in the same envelope.

A single agent with a tight tool set still beats most three-worker graphs on cost and latency. Supervisor is not a free upgrade.

## What “good” looks like

From the skill + Anthropic + 2026 production practice:

- Hard **step / turn / token budget in code**, not in a prompt
- **Explicit schemas** on every tool and every worker return
- **HITL** before delete, pay, send, deploy, PII
- Stronger model on plan + synthesize only; cheap models on workers
- Code router or DAG when next-hop is enumerable
- Stay single-agent + tools until context isolation is proven
- Log model, tokens, latency, tool calls, outcome

Anti-patterns: unbounded loops; business logic only in prompts; silent tool failure; swarm without a progress key; supervisor for a linear pipeline.

## How Superdeterminism uses this

We do **not** search a new graph (MaAS / AFlow). We do **not** lint harness files (AgentLint). We re-type nodes — and the orchestrator — on traces. See [type-lattice.md](type-lattice.md).

Unsafe: “nobody advises workflow vs agent.” Anthropic already does. Safe: nobody does that *re-type on an ingested production graph* with counterfactual evidence.

Bibliography: [references.md](references.md).
