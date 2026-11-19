#!/usr/bin/env python3
"""Fail if any dependency in package.json is not pinned to an exact version."""
import json
import re
import sys
from pathlib import Path

pkg = json.loads((Path(__file__).resolve().parent.parent / "package.json").read_text("utf-8"))
bad = [f"{section}: {name}@{spec}" for section in ("dependencies", "devDependencies", "optionalDependencies")
       for name, spec in pkg.get(section, {}).items() if not re.fullmatch(r"\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?", spec)]
for name in ("@microsoft/powerbi-report-authoring-cli", "@microsoft/powerbi-core-visual-schema"):
    if name not in pkg.get("dependencies", {}):
        bad.append(f"{name} is missing from dependencies")
if bad:
    print("package.json must pin exact versions (no ^, ~, ranges or tags):\n  " + "\n  ".join(bad), file=sys.stderr)
    sys.exit(1)
print("All dependencies are pinned to exact versions.")
