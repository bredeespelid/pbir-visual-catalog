#!/usr/bin/env python3
"""Print a compact Markdown brief for a visual type, ready to paste into an agent prompt.

Usage:
  python3 scripts/visual_brief.py barChart
  python3 scripts/visual_brief.py --list
  python3 scripts/visual_brief.py barChart --catalog path/to/catalog
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_visual_catalog import ExportError, find_repo_root  # noqa: E402


def bounds(b: dict) -> str:
    lo, hi = b.get("min"), b.get("max")
    if hi == 0:
        return "must be empty"
    if lo is not None and hi is not None:
        return f"exactly {lo}" if lo == hi else f"{lo}-{hi}"
    if lo is not None:
        return f">= {lo}"
    return f"<= {hi}"


def brief(v: dict) -> str:
    out = [f"# {v['visualType']}"]
    if v["deprecated"]:
        alt = v.get("alternative")
        out.append(f"**DEPRECATED**{f' - use `{alt}` instead' if alt else ''}. {v.get('deprecationReason', '')}".strip())
    out += ["", "## Data roles (queryState keys)", "",
            "| Role | Kind | Required | Max fields | Notes |", "|---|---|---|---|---|"]
    for name, r in v["roles"].items():
        notes = []
        for k in ("requiredTypes", "preferredTypes", "noDuplicates"):
            if k in r:
                notes.append(f"{k}={json.dumps(r[k], separators=(',', ':'))}")
        out.append(f"| `{name}` ({r['displayName']}) | {r['kind']} | {'yes' if r['required'] else 'no'} | "
                   f"{r['maxItems'] if r['maxItems'] is not None else 'any'} | {'; '.join(notes)} |")
    if v["roleCombinations"]:
        out += ["", "## Allowed role combinations (at least one must hold; unlisted roles unconstrained)", ""]
        for i, combo in enumerate(v["roleCombinations"], 1):
            out.append(f"{i}. " + ", ".join(f"`{r}` {bounds(b)}" for r, b in combo.items()))
    out += ["", "## Formatting objects (`visual.objects` keys)", "", ", ".join(f"`{o}`" for o in v["formattingObjects"])]
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("visual_type", nargs="?")
    ap.add_argument("--list", action="store_true", help="list available visual types")
    ap.add_argument("--catalog", type=Path, help="catalog directory (default: <repo root>/catalog)")
    args = ap.parse_args()
    try:
        cat = args.catalog or find_repo_root(Path(__file__).resolve().parent) / "catalog"
    except ExportError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    index = json.loads((cat / "index.json").read_text("utf-8"))
    names = [v["visualType"] for v in index["visuals"]]
    if args.list or not args.visual_type:
        print("\n".join(names))
        return 0
    if args.visual_type not in names:
        print(f"Unknown visual type {args.visual_type!r}. Run with --list.", file=sys.stderr)
        return 1
    print(brief(json.loads((cat / "visuals" / f"{args.visual_type}.json").read_text("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
