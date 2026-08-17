from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from superdeterminism.adapters import AdapterError, resolve
from superdeterminism.models import Action
from superdeterminism.scaffold import write_scaffold
from superdeterminism.pipeline import (
    N_MIN_DEFAULT,
    load_traces_path,
    recommend_full,
    recommendations_to_dict,
    recommendations_to_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="superdeterminism",
        description="Agnostic determinism advisor. JSON in/out. No prompts. No auto-apply.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    rec = sub.add_parser("recommend", help="ingest traces and emit L0 recommendations")
    rec.add_argument(
        "traces",
        type=Path,
        nargs="?",
        default=None,
        help="OTLP JSON or advisor {traces:[...]}",
    )
    rec.add_argument(
        "--traces-dir",
        type=Path,
        default=None,
        help="load every *.json in DIR; one report",
    )
    rec.add_argument("--json", dest="json_out", type=Path, default=None)
    rec.add_argument("--md", dest="md_out", type=Path, default=None)
    rec.add_argument("--n-min", type=int, default=N_MIN_DEFAULT)
    rec.add_argument(
        "--stdout",
        choices=("json", "md"),
        default="json",
        help="print this format to stdout (agents: json)",
    )
    rec.add_argument(
        "--adapter",
        default=None,
        help="optional ingest adapter (e.g. langgraph). omitted = P0 generic ingest",
    )
    rec.add_argument(
        "--opt-in-l1",
        action="store_true",
        help="opt-in L1 on high-EV candidates; warns; no live call unless SUPERDETERMINISM_L1_MODEL",
    )
    scaf = sub.add_parser("scaffold", help="write illustrative scaffold; never edits user source")
    scaf.add_argument("report", type=Path, help="recommend JSON report")
    scaf.add_argument("--out", type=Path, required=True, help="directory to write (created)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "scaffold":
        return _scaffold(args)
    if args.cmd != "recommend":
        return 2
    try:
        traces = _load_recommend_input(args)
        recs, orch = recommend_full(traces, n_min=args.n_min)
    except AdapterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    payload = recommendations_to_dict(recs, orchestrator=orch)
    payload = apply_l1(payload, opt_in=args.opt_in_l1)
    markdown = recommendations_to_markdown(recs, orchestrator=orch)
    if args.json_out:
        args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.md_out:
        args.md_out.write_text(markdown, encoding="utf-8")
    if args.stdout == "json":
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(markdown)
        if not markdown.endswith("\n"):
            sys.stdout.write("\n")
    # ponytail: nonzero only on input failure; ABSTAIN is a valid report
    _ = Action
    return 0


L1_MODEL_ENV = "SUPERDETERMINISM_L1_MODEL"
_L1_WARNING = (
    "warning: simulation != production; --opt-in-l1 is not a production A/B test"
)


def call_model(prompt: str) -> str:
    # ponytail: live tail not implemented; symbol exists so tests can assert it is not called
    raise RuntimeError("live L1 tail is not implemented")


def apply_l1(payload: dict, *, opt_in: bool) -> dict:
    if not opt_in:
        return payload
    print(_L1_WARNING, file=sys.stderr)
    note = (
        "L1 model configured; live tail not implemented; no network"
        if os.environ.get(L1_MODEL_ENV)
        else "L1 requested; no SUPERDETERMINISM_L1_MODEL; no live call"
    )
    if os.environ.get(L1_MODEL_ENV):
        # reserved: call_model() only when a live tail exists
        _ = call_model
    for row in payload.get("recommendations") or []:
        if row.get("action") != "ABSTAIN":
            row.setdefault("reasons", []).append(note)
    return payload


def _load_recommend_input(args: argparse.Namespace):
    paths: list[Path]
    if args.traces_dir is not None:
        if not args.traces_dir.is_dir():
            raise ValueError(f"not a directory: {args.traces_dir}")
        paths = sorted(args.traces_dir.glob("*.json"))
        if not paths:
            raise ValueError(f"no *.json in {args.traces_dir}")
    elif args.traces is not None:
        paths = [args.traces]
    else:
        raise ValueError("provide a traces file or --traces-dir")
    loader = resolve(args.adapter) if args.adapter else load_traces_path
    traces = []
    for path in paths:
        traces.extend(loader(path))
    return traces


def _scaffold(args: argparse.Namespace) -> int:
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            raise ValueError("report must be a JSON object")
        write_scaffold(report, args.out)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
