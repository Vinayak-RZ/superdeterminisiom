"""Write illustrative scaffold files. Never mutates user source."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from superdeterminism.models import Action

_REFUSE = ("send", "command", "interrupt", "checkpointer")
_DISCLAIMER = (
    "Copy these files by hand. Do not apply this patch to graph.py automatically. "
    "simulation != production; canary is confirmatory."
)


def write_scaffold(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    recs = list(report.get("recommendations") or [])
    (out_dir / "REPORT.md").write_text(_report_md(report, recs), encoding="utf-8")
    (out_dir / "WIRING.md").write_text(_wiring_md(recs), encoding="utf-8")
    patchable = [r for r in recs if _wants_patch(r)]
    if not patchable:
        return
    patches = out_dir / "patches"
    patches.mkdir(exist_ok=True)
    for rec in patchable:
        name = _safe_name(str(rec.get("node_id") or "node"))
        (patches / f"{name}.diff").write_text(_diff_for(rec), encoding="utf-8")


def _wants_patch(rec: dict[str, Any]) -> bool:
    action = rec.get("action")
    if action in {Action.ABSTAIN.value, "ABSTAIN", None}:
        return False
    blob = " ".join(
        [str(rec.get("node_id") or ""), *map(str, rec.get("reasons") or [])]
    ).lower()
    return not any(token in blob for token in _REFUSE)


def _safe_name(node_id: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in node_id) or "node"


def _report_md(report: dict[str, Any], recs: list[dict[str, Any]]) -> str:
    lines = [
        "# Determinism Advisor scaffold",
        "",
        f"> {_DISCLAIMER}",
        "",
        f"estimator: {report.get('estimator', 'observational_l0_proxy')}",
        "",
    ]
    for rec in recs:
        lines.append(f"## {rec.get('node_id')} — {rec.get('action')}")
        for reason in rec.get("reasons") or []:
            lines.append(f"- {reason}")
        lines.append("")
    return "\n".join(lines)


def _wiring_md(recs: list[dict[str, Any]]) -> str:
    lines = [
        "# Wiring",
        "",
        "Keep the node name. Change the callable. Human (or a coding agent) copies the diff.",
        "",
        "Use `langchain.agents.create_agent`. Do not emit the deprecated ReAct prebuilt.",
        "",
    ]
    for rec in recs:
        node = rec.get("node_id")
        action = rec.get("action")
        lines.append(f"- `{node}`: {action} — edit `add_node(\"{node}\", ...)` or `tools=`")
    lines.append("")
    return "\n".join(lines)


def _diff_for(rec: dict[str, Any]) -> str:
    node = str(rec.get("node_id") or "node")
    action = rec.get("action")
    if action == Action.FLIP_TO_DET.value:
        return (
            f"- builder.add_node(\"{node}\", llm_{node})\n"
            f"+ builder.add_node(\"{node}\", {node})  # generated/nodes/{node}.py\n"
        )
    if action == Action.FLIP_TO_NONDET.value:
        return (
            f"- builder.add_node(\"{node}\", ToolNode([{node}_regex]))\n"
            f"+ builder.add_node(\"{node}\", {node})  # create_agent subgraph "
            f"(proposer/verifier/commit/reject)\n"
        )
    # STRENGTHEN_SDB
    return (
        f"  builder.add_node(\"{node}\", {node}_proposer)\n"
        f"+ builder.add_node(\"{node}_gate\", {node}_gate)  # deterministic gate stub\n"
    )
