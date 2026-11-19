#!/usr/bin/env python3
"""Generate the PBIR visual catalog from Microsoft's official npm packages.

Sources (both MIT, pinned in package.json):
  * @microsoft/powerbi-report-authoring-cli  ->  `powerbi-report-author catalog list|describe`
  * @microsoft/powerbi-core-visual-schema     ->  data/capabilities.json

Output (default: <repo>/catalog):
  index.json                 all visual types + source versions + generation timestamp
  visuals/<visualType>.json  one file per visual type

Usage:
  npm ci
  python3 scripts/export_visual_catalog.py [--output DIR]

Exit codes: 0 ok, 1 export failed (most likely an API/format change on
Microsoft's side - see the error message).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CLI_PKG = "@microsoft/powerbi-report-authoring-cli"
SCHEMA_PKG = "@microsoft/powerbi-core-visual-schema"
CLI_BIN = "powerbi-report-author"
CAPS_REL = Path("data") / "capabilities.json"
FORMAT_VERSION = 1

# Keys we rely on in the CLI's `catalog describe` payload.
DESCRIBE_KEYS = {"visualType", "capabilityKey", "roles", "requiredRoles", "optionalRoles",
                 "maxPerRole", "formattingObjects", "deprecated"}
# Role-level fields copied from capabilities.json (the CLI does not expose them).
RAW_ROLE_FIELDS = ("requiredTypes", "preferredTypes", "noDuplicates")

HINT = ("This usually means Microsoft changed the output format of "
        f"{CLI_PKG} or {SCHEMA_PKG}. Compare the two versions in package.json "
        "with their previous releases, then adapt scripts/export_visual_catalog.py.")


class ExportError(Exception):
    pass


def find_repo_root(start: Path) -> Path:
    for d in [start, *start.parents]:
        if (d / "package.json").is_file():
            return d
    raise ExportError(f"Could not locate the repo root (no package.json above {start}).")


def package_dir(root: Path, pkg: str) -> Path:
    d = root / "node_modules" / Path(*pkg.split("/"))
    if not (d / "package.json").is_file():
        raise ExportError(f"{pkg} is not installed in {root}/node_modules. Run `npm ci` first.")
    return d


def package_version(root: Path, pkg: str) -> str:
    return json.loads((package_dir(root, pkg) / "package.json").read_text("utf-8"))["version"]


class Cli:
    def __init__(self, root: Path):
        self.bin = shutil.which(CLI_BIN, path=str(root / "node_modules" / ".bin"))
        if not self.bin:
            raise ExportError(f"`{CLI_BIN}` not found in node_modules/.bin. Run `npm ci` first.")

    def run(self, *args: str) -> dict:
        proc = subprocess.run([self.bin, *args], capture_output=True, text=True, timeout=120)
        label = f"{CLI_BIN} {' '.join(args)}"
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise ExportError(f"`{label}` did not return JSON (exit {proc.returncode}). "
                              f"stderr: {proc.stderr.strip()[:300]!r}. {HINT}")
        if not isinstance(payload, dict):
            raise ExportError(f"`{label}` returned unexpected JSON type {type(payload).__name__}. {HINT}")
        if "error" in payload:
            err = payload["error"]
            raise ExportError(f"`{label}` returned an error: {err.get('code')}: {err.get('message')}")
        if not isinstance(payload.get("data"), dict):
            raise ExportError(f"`{label}` output has no `data` object. {HINT}")
        return payload["data"]


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def build_visual(desc: dict, raw: dict | None, dep: dict | None) -> dict:
    missing = DESCRIBE_KEYS - desc.keys()
    if missing:
        raise ExportError(f"`catalog describe {desc.get('visualType')}` is missing keys "
                          f"{sorted(missing)}. {HINT}")
    raw_roles = {r["name"]: r for r in (raw or {}).get("dataRoles", []) if "name" in r}
    required = set(desc["requiredRoles"])
    max_per_role = desc["maxPerRole"]

    roles = {}
    for name, role in desc["roles"].items():
        entry = {
            "kind": role.get("kind"),
            "displayName": role.get("displayName"),
            "description": role.get("description"),
            "required": name in required,
            "maxItems": max_per_role.get(name),
        }
        for field in RAW_ROLE_FIELDS:
            if field in raw_roles.get(name, {}):
                entry[field] = raw_roles[name][field]
        roles[name] = entry

    # Allowed role combinations: any ONE alternative must hold; roles not
    # mentioned in an alternative are unconstrained.
    combos: dict[str, dict] = {}
    for mapping in (raw or {}).get("dataViewMappings", []):
        for cond in mapping.get("conditions", []):
            combos[canonical(cond)] = cond

    visual = {
        "visualType": desc["visualType"],
        "deprecated": bool(desc["deprecated"]),
    }
    if dep:
        if dep.get("alternative"):
            visual["alternative"] = dep["alternative"]
        if dep.get("reason"):
            visual["deprecationReason"] = dep["reason"]
    visual.update({
        "requiredRoles": list(desc["requiredRoles"]),
        "optionalRoles": list(desc["optionalRoles"]),
        "roles": roles,
        "roleCombinations": [combos[k] for k in sorted(combos)],
        "formattingObjects": list(desc["formattingObjects"]),
        "sharedCapabilitiesWith": list(desc.get("sharedCapabilitiesWith", [])),
    })
    return visual


def dump(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def export(root: Path, output: Path) -> dict:
    cli = Cli(root)
    versions = {CLI_PKG: package_version(root, CLI_PKG), SCHEMA_PKG: package_version(root, SCHEMA_PKG)}

    caps_path = package_dir(root, SCHEMA_PKG) / CAPS_REL
    if not caps_path.is_file():
        raise ExportError(f"{SCHEMA_PKG}@{versions[SCHEMA_PKG]} no longer ships {CAPS_REL}. {HINT}")
    caps = json.loads(caps_path.read_text("utf-8"))
    if not isinstance(caps, dict) or len(caps) < 10:
        raise ExportError(f"{CAPS_REL} has an unexpected shape. {HINT}")

    listing = cli.run("catalog", "list")
    types = listing.get("visualTypes")
    if not isinstance(types, list) or not types:
        raise ExportError(f"`catalog list` returned no visualTypes. {HINT}")
    deprecated = {d["visualType"]: d for d in listing.get("deprecated", [])}

    visuals = {}
    for t in sorted(types):
        desc = cli.run("catalog", "describe", t)
        raw = caps.get(desc.get("capabilityKey", t))
        if raw is None:
            raise ExportError(f"No entry for capability key {desc.get('capabilityKey', t)!r} in "
                              f"{CAPS_REL} (visual type {t}). {HINT}")
        visuals[t] = build_visual(desc, raw, deprecated.get(t))

    skipped = [{"capabilityKey": k, "reason": "Present in capabilities.json but unknown to the authoring CLI"}
               for k in sorted(set(caps) - set(types) - {"_metadata"})]

    files = {f"visuals/{t}.json": dump(v) for t, v in visuals.items()}
    index = {
        "formatVersion": FORMAT_VERSION,
        "sources": {pkg: {"version": v, "license": "MIT"} for pkg, v in versions.items()},
        "visualTypeCount": len(visuals),
        "skipped": skipped,
        "visuals": [
            {"visualType": t, "file": f"visuals/{t}.json", "deprecated": v["deprecated"],
             **({"alternative": v["alternative"]} if "alternative" in v else {}),
             "requiredRoles": v["requiredRoles"], "optionalRoles": v["optionalRoles"]}
            for t, v in visuals.items()
        ],
    }

    # Keep the old timestamp unless content actually changed -> no noisy commits.
    digest = hashlib.sha256(("".join(files[k] for k in sorted(files)) + canonical(index)).encode()).hexdigest()
    old_index = None
    if (output / "index.json").is_file():
        try:
            old_index = json.loads((output / "index.json").read_text("utf-8"))
        except json.JSONDecodeError:
            pass
    if old_index and old_index.get("contentSha256") == digest:
        generated_at = old_index["generatedAt"]
    else:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    index = {"generatedAt": generated_at, "contentSha256": digest, **index}

    # Write.
    (output / "visuals").mkdir(parents=True, exist_ok=True)
    for stale in (output / "visuals").glob("*.json"):
        if f"visuals/{stale.name}" not in files:
            stale.unlink()
    for rel, text in files.items():
        (output / rel).write_text(text, encoding="utf-8")
    (output / "index.json").write_text(dump(index), encoding="utf-8")

    # Report added/removed types as a warning, not a failure.
    if old_index:
        before = {v["visualType"] for v in old_index.get("visuals", [])}
        added, removed = sorted(set(visuals) - before), sorted(before - set(visuals))
        if added or removed:
            msg = f"Visual types changed. Added: {added or 'none'}. Removed: {removed or 'none'}."
            print(f"::warning title=Visual types changed::{msg}" if os.environ.get("GITHUB_ACTIONS") else msg)
            summary = os.environ.get("GITHUB_STEP_SUMMARY")
            if summary:
                with open(summary, "a", encoding="utf-8") as fh:
                    fh.write(f"### Visual types changed\n- Added: {added or 'none'}\n- Removed: {removed or 'none'}\n")
    return index


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", type=Path, help="output directory (default: <repo root>/catalog)")
    args = ap.parse_args(argv)
    try:
        root = find_repo_root(Path(__file__).resolve().parent)
        output = (args.output or root / "catalog").resolve()
        index = export(root, output)
    except ExportError as e:
        title = "Catalog export failed (possible upstream API change)"
        print(f"::error title={title}::{e}" if os.environ.get("GITHUB_ACTIONS") else f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"Exported {index['visualTypeCount']} visual types to {output} "
          f"(generatedAt {index['generatedAt']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
