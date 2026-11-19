#!/usr/bin/env python3
"""Fail if docs/choosing-a-visual.md names a visual type that is unknown or deprecated.

Every backticked token inside a Markdown table row of that file must be a non-deprecated
visual type in catalog/index.json, except the words in IGNORE.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "choosing-a-visual.md"
IGNORE = {"filledMap", "map"}  # mentioned only as deprecated, with the replacement
index = {v["visualType"]: v for v in json.loads((ROOT / "catalog" / "index.json").read_text("utf-8"))["visuals"]}

problems = []
for n, line in enumerate(DOC.read_text("utf-8").splitlines(), 1):
    if not line.startswith("|"):
        continue
    for token in re.findall(r"`([^`]+)`", line):
        if token in IGNORE or token in {"Size", "Series", "Grouping", "Measure"}:
            continue
        if re.fullmatch(r"[a-z][A-Za-z]+", token) and token not in index:
            problems.append(f"{DOC.name}:{n}: unknown visual type `{token}`")
        elif token in index and index[token]["deprecated"]:
            problems.append(f"{DOC.name}:{n}: `{token}` is deprecated")
if problems:
    print("\n".join(problems), file=sys.stderr)
    sys.exit(1)
print("docs/choosing-a-visual.md only references valid, non-deprecated visual types.")
