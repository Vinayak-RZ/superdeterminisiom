from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from superdeterminism.adapters import AdapterError, resolve
from superdeterminism.models import Action
from superdeterminism.pipeline import (
    N_MIN_DEFAULT,
    load_traces_path,
    recommend_traces,
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
    rec.add_argument("traces", type=Path, help="OTLP JSON or advisor {traces:[...]}")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd != "recommend":
        return 2
    try:
        if args.adapter:
            traces = resolve(args.adapter)(args.traces)
        else:
            traces = load_traces_path(args.traces)
        recs = recommend_traces(traces, n_min=args.n_min)
    except AdapterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    payload = recommendations_to_dict(recs)
    markdown = recommendations_to_markdown(recs)
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


if __name__ == "__main__":
    raise SystemExit(main())
