#!/usr/bin/env python3
"""Fail if the committed catalog/ differs from a fresh export.

Regenerates the catalog into a temporary directory from the installed (pinned)
npm packages and compares it with catalog/. `generatedAt` is ignored.

Usage: npm ci && python3 scripts/check_catalog.py
"""
from __future__ import annotations

import difflib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_visual_catalog as ex  # noqa: E402


def load(directory: Path) -> dict[str, str]:
    out = {}
    for p in sorted(directory.rglob("*.json")):
        text = p.read_text("utf-8")
        if p.name == "index.json":
            data = json.loads(text)
            data.pop("generatedAt", None)
            text = ex.dump(data)
        out[p.relative_to(directory).as_posix()] = text
    return out


def main() -> int:
    try:
        root = ex.find_repo_root(Path(__file__).resolve().parent)
        with tempfile.TemporaryDirectory() as tmp:
            ex.export(root, Path(tmp))
            fresh = load(Path(tmp))
    except ex.ExportError as e:
        print(f"ERROR: export failed: {e}", file=sys.stderr)
        return 1
    committed_dir = root / "catalog"
    committed = load(committed_dir) if committed_dir.is_dir() else {}

    problems = []
    for name in sorted(fresh.keys() | committed.keys()):
        if name not in committed:
            problems.append(f"missing from catalog/: {name}")
        elif name not in fresh:
            problems.append(f"stale file in catalog/: {name}")
        elif fresh[name] != committed[name]:
            diff = difflib.unified_diff(committed[name].splitlines(), fresh[name].splitlines(),
                                        "committed", "regenerated", lineterm="", n=1)
            problems.append(f"differs: {name}\n" + "\n".join(list(diff)[:20]))
    if problems:
        print("catalog/ is out of date:\n\n" + "\n\n".join(problems), file=sys.stderr)
        print("\nFix: run `npm ci && npm run catalog:build` and commit the result.", file=sys.stderr)
        return 1
    print(f"catalog/ is up to date ({len(fresh) - 1} visual types).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
