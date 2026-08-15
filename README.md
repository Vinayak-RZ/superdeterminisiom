# superdeterminism

Working title: **Determinism Advisor**.

Take production agent traces, reconstruct the architecture graph, then for ambiguous steps estimate what would happen if an LLM/subagent node were a deterministic tool/function instead (and vice versa). Report deltas in cost, latency, failure rate, output variance, auditability, and policy compliance. Recommend a refactor — with confidence intervals and an explicit “simulation ≠ production” banner.

## Methodology

The scientific design — Causal Agent Replay, CausalFlow, Tracefork, AgentReplay, Shapley ablation, WHEN2TOOL / To Call or Not to Call, LangGraph time-travel as it actually works, cheap approximations when you cannot re-run the LLM, threats to validity, and the v0 algorithm — is in:

**[docs/methodology.md](docs/methodology.md)**
