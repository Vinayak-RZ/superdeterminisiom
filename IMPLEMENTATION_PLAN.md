# P3 role lattice + orchestrator — nawab execution contract

Approved feature-mode plan. Authority: [docs/type-lattice.md](docs/type-lattice.md), [docs/orchestrator.md](docs/orchestrator.md), [docs/decisions/0005-architecture-role-lattice.md](docs/decisions/0005-architecture-role-lattice.md).

---

## §0 Plan metadata

| Field | Value |
|-------|-------|
| **Mode** | feature |
| **Stack** | Python 3.10+, stdlib core |
| **Base branch** | `cursor/oss-polish-readme-329f` |
| **Feature branch** | `cursor/p3-architecture-lattice-329f` |
| **Estimated commits** | 4–6 |

---

## §1 North star

Widen Superdeterminism from tool-vs-LLM to architectural-role advisor. Track the orchestrator as a graph-level object. Keep ingest → L0 → recommend. No auto-apply. No invented `gen_ai.*`.

---

## §15 Cutover

Done when extras-free pytest is green and the stacked PR is open.
