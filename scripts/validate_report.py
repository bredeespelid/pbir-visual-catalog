#!/usr/bin/env python3
"""Validate PBIR report folders against Microsoft's schemas AND this catalog.

1. Runs `powerbi-report-author validate` (pinned in package.json). Fails on any
   error, and - unlike the CLI - also on warnings, in particular
   PBIR_SCHEMA_UNREACHABLE (schema could not be downloaded, so nothing was
   actually checked). Use --offline to allow that for local runs.
2. Checks every visual.json against catalog/: known, non-deprecated visualType,
   known roles, required roles present, per-role max, allowed role combinations.

Usage: python3 scripts/validate_report.py [REPORT_DIR ...] [--offline]
Default: every *.Report folder under examples/.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_visual_catalog import ExportError, find_repo_root  # noqa: E402


def run_cli(root: Path, report: Path, offline: bool) -> list[str]:
    cli = shutil.which("powerbi-report-author", path=str(root / "node_modules" / ".bin"))
    if not cli:
        raise ExportError("powerbi-report-author not installed. Run `npm ci` first.")
    cmd = [cli, "validate", str(report)] + (["--no-schema"] if offline else [])
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    try:
        data = json.loads(proc.stdout)["data"]
    except (json.JSONDecodeError, KeyError):
        return [f"CLI validate returned unusable output (exit {proc.returncode}): {proc.stdout[:200]!r} {proc.stderr[:200]!r}"]
    problems = []
    for code, group in data.get("diagnostics", {}).items():
        for item in group.get("items", []):
            problems.append(f"[{group.get('severity')}] {code}: {item.get('message')}")
    if data.get("errorCount") == 0 and data.get("warningCount") == 0:
        return []
    return problems or [f"validate result: {data.get('result')}"]


def bounds_ok(n: int, b: dict) -> bool:
    return n >= b.get("min", 0) and n <= b.get("max", float("inf"))


def check_visual(path: Path, catalog: Path) -> list[str]:
    doc = json.loads(path.read_text("utf-8"))
    visual = doc.get("visual")
    if not visual:  # visual groups have no `visual` object
        return []
    vt = visual.get("visualType")
    cat_file = catalog / "visuals" / f"{vt}.json"
    if not cat_file.is_file():
        return [f"{vt!r} is not in the catalog"]
    cat = json.loads(cat_file.read_text("utf-8"))
    errs = []
    if cat["deprecated"]:
        errs.append(f"{vt} is deprecated" + (f" (use {cat['alternative']})" if "alternative" in cat else ""))
    state = visual.get("query", {}).get("queryState", {})
    counts = {role: len(v.get("projections", [])) for role, v in state.items()}
    for role in counts:
        if role not in cat["roles"]:
            errs.append(f"unknown role {role!r} (valid: {', '.join(cat['roles'])})")
    for role in cat["requiredRoles"]:
        if counts.get(role, 0) == 0:
            errs.append(f"required role {role!r} is empty")
    for role, n in counts.items():
        mx = cat["roles"].get(role, {}).get("maxItems")
        if mx is not None and n > mx:
            errs.append(f"role {role!r} has {n} fields, max is {mx}")
    combos = cat["roleCombinations"]
    if combos and not any(all(bounds_ok(counts.get(r, 0), b) for r, b in c.items()) for c in combos):
        errs.append(f"role field counts {counts} match none of the allowed combinations")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reports", nargs="*", type=Path)
    ap.add_argument("--offline", action="store_true", help="skip remote schema validation (local use only)")
    args = ap.parse_args()
    try:
        root = find_repo_root(Path(__file__).resolve().parent)
        reports = args.reports or sorted((root / "examples").glob("**/*.Report"))
        if not reports:
            print("ERROR: no *.Report folders found", file=sys.stderr)
            return 1
        failed = False
        for report in reports:
            problems = [f"schema: {p}" for p in run_cli(root, report, args.offline)]
            for vf in sorted((report / "definition").glob("**/visuals/*/visual.json")):
                problems += [f"{vf.relative_to(report)}: {e}" for e in check_visual(vf, root / "catalog")]
            if problems:
                failed = True
                print(f"FAIL {report}", file=sys.stderr)
                for p in problems:
                    print(f"  - {p}", file=sys.stderr)
            else:
                print(f"OK   {report}")
        return 1 if failed else 0
    except ExportError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
