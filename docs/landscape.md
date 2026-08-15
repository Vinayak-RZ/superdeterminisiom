# Landscape

**Dated 2026-08-15.** Adjacent tools will keep shipping. Re-check citations before treating this as current.

This document exists so we do not claim false whitespace.

## The claim we make

No shipping product takes production traces, reconstructs the agent graph (including the control-flow owner), and recommends *architectural-role* refactors (workflow ↔ subagent ↔ tool ↔ router ↔ LLM, plus orchestrator bound/collapse/code-route) backed by counterfactual evidence.

Differentiation:

> Counterfactual *re-typing* of nodes — and of the orchestrator that owns control flow — on ingested production graphs — not “score the path you already ran,” and not “search a new workflow from scratch.”

Determinism-class (tool ↔ LLM) is a *subset* of that lattice.

## Claims we will not make

Do **not** say “nobody does counterfactual agent simulation.” CAR, CausalFlow, Tracefork, AgentReplay, and counterfact already intervene on traces.

Do **not** say “nobody does agent architecture search.” MaAS, AFlow, ScoreFlow, ADAS, EvoAgentX exist. They search operator graphs offline; they do not ingest a production graph and re-type roles.

Do **not** say “nobody lints agent architecture.” AgentLint, isolint, ArchRails, and arch-advisor lint harness files or interview the user. They do not simulate flips on traces.

Do **not** say “nobody advises tool vs LLM.” WHEN2TOOL, MeCo, and “To Call or Not to Call” decide *at generation time* whether to emit a tool call. Galileo Tool Selection Quality scores a turn. None output “refactor node X from `invoke_agent` to `execute_tool`.”

Do **not** say “nobody advises workflow vs agent.” Anthropic’s [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) *is* that doctrine.

Do **not** say “nobody does multi-agent orchestration.” LangGraph supervisor, CrewAI, MAF, and the OpenAI Agents SDK already do.

## Closeness matrix

| System | Ingest traces | Map architecture | Simulate counterfactuals | Recommend refactor | Flip **role** (incl. hub) |
|---|---|---|---|---|---|
| LangSmith + LangGraph time-travel | Yes | Partial | Manual fork | No | No |
| AgentEvals / OpenEvals | Via LangSmith | No | No | No | No |
| MLflow genai | Yes | No | User-sim only | No | No |
| DeepEval / Confident AI | Yes | No | No | No | No |
| Galileo / Splunk | Yes | Graph view | No | Code-fix agent | Turn-level “tool needed?” |
| Langfuse | Yes | No | No | No | No |
| Phoenix / Braintrust / Opik | Yes | Weak | No | Prompt/schema opt (Opik) | No |
| Foundry Agent Optimizer | Yes | No | Config search | Prompt/skill diffs | No |
| **CAR** | Yes | Implicit SCM | Yes (`do_*`) | Attribution only | No |
| **CausalFlow** | Yes (typed steps) | Step chain | Yes | Step repairs | No (typed, not re-typed) |
| **Tracefork** | Cassette | No | Yes (fork + blame) | Blame ranking | No |
| **AgentReplay** | Cassette | No | Yes (mutate) | No | No |
| **counterfact** | Instrumented graph | Yes (nodes) | Yes (ablate) | Yes (Shapley fixes) | No |
| MaAS / AFlow / EvoAgentX | No | Search space | Offline eval | Yes (new graph) | Indirect |
| AgentLint / arch-advisor | No (files / interview) | Harness | No | File/ADR advice | Doctrinal only |
| WHEN2TOOL / MeCo | Hidden states | No | No | Runtime steer | Decode-time only |
| OTel GenAI spec | Schema | `execute_tool` vs `invoke_agent` | No | No | Schema only |

Nothing has Yes in the last column **and** ingest-traces **and** recommend-refactor.

## Closest neighbors

**Causal Agent Replay (CAR)** — [arXiv:2606.08275](https://arxiv.org/abs/2606.08275), [jaineet17/causal-agent-replay](https://github.com/jaineet17/causal-agent-replay). Models a run as an SCM. `do_policy` is the flip we want, but CAR attributes *failure*, it does not recommend “make this node a tool.” Closest research system on the simulation axis.

**CausalFlow** — [arXiv:2605.25338](https://arxiv.org/abs/2605.25338). Typed steps (`REASONING`, `TOOL_CALL`, `LLM_RESPONSE`, …). Repairs step *content*, not node type. The type tags are a natural hook.

**Tracefork** / **AgentReplay** — content-addressed tape / VCR cassette. The L0/L1 engine we would want under a flip simulator. They do not search architectures.

**counterfact** — [counterfact-labs/counterfact](https://github.com/counterfact-labs/counterfact). Ablates agents, Shapley attribution, fix recommendations. Closest product-shaped OSS on “recommend a change.” Wrong intervention: remove/degrade a node, do not re-type it.

**WHEN2TOOL** — [arXiv:2605.09252](https://arxiv.org/abs/2605.09252). Necessity is decodable from hidden states. Runtime policy, not architecture advice.

**Eval platforms** — LangSmith, MLflow, DeepEval Tool Correctness, Galileo Tool Selection Quality, Langfuse. Observe and score. DeepEval’s Tool Correctness is the closest *conceptual* split (deterministic tool check vs LLM-judged steps) and is still testing infrastructure.

## How to talk about this

Safe: “No product re-types architectural roles (including the orchestrator) on an ingested production graph and recommends a refactor.”

Unsafe: “Nobody does counterfactual traces / architecture search / tool-correctness / when-to-use-an-agent advising / agent simulation / orchestration / workflow-vs-agent advising.” Those phrases already belong to other products (and “simulation” often means *user* simulation).

Full bibliography: [references.md](references.md).
