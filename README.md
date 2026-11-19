# pbir-visual-catalog

A **machine-readable catalog of Power BI visuals (PBIR)** that you can clone and hand to an AI agent
(Claude Code, GitHub Copilot, ...) to build correct reports - "vibe-coding" Power BI without the agent
guessing role names, field limits or formatting objects.

- `catalog/visuals/<visualType>.json` - one file per visual type (57): data roles, required/optional,
  max fields per role, type requirements, allowed role combinations, formatting objects, deprecation info.
- `catalog/index.json` - all types plus the exact source package versions and generation timestamp.
- `examples/minimal-report` - a small PBIP project (card, slicer, bar chart) built from the catalog.
- `AGENTS.md` - instructions that tell an agent how to look up a visual and write a valid `visual.json`.

> **Generated content.** Everything in `catalog/` is generated from Microsoft's official, MIT-licensed npm packages,
> pinned to exact versions in `package.json`:
> - [`@microsoft/powerbi-report-authoring-cli`](https://www.npmjs.com/package/@microsoft/powerbi-report-authoring-cli) (`powerbi-report-author catalog describe <visualType>`)
> - [`@microsoft/powerbi-core-visual-schema`](https://www.npmjs.com/package/@microsoft/powerbi-core-visual-schema) (`data/capabilities.json`)
>
> Source: [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric). This project is not affiliated with
> or endorsed by Microsoft. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
> Both packages are `0.x` previews, so formats may change - that is exactly what the automation below watches for.

## Use it with an AI agent

```bash
git clone https://github.com/bredeespelid/pbir-visual-catalog.git
cd pbir-visual-catalog
npm ci          # installs the pinned Microsoft CLI (needed for validation)
```

- **Claude Code:** run `claude` in the folder. `CLAUDE.md` points to `AGENTS.md` automatically.
  Try: *"Add a page to examples/minimal-report with a line chart of Amount by Region and validate it."*
- **GitHub Copilot (VS Code / coding agent):** `.github/copilot-instructions.md` points to `AGENTS.md`.
- **Your own project:** copy `catalog/` and `AGENTS.md` into your PBIP repo (or add this repo as a submodule) and
  tell the agent to follow `AGENTS.md`.

Without an agent: `python3 scripts/visual_brief.py barChart` prints a compact brief for any visual type.

## Requirements

Node >= 20.10 and Python >= 3.10 (standard library only). Opening a report in Power BI Desktop needs Windows.

## Regenerate / verify

```bash
npm ci
npm run catalog:build      # regenerate catalog/ (python3 scripts/export_visual_catalog.py [--output DIR])
npm run catalog:check      # fail if catalog/ is stale
npm run examples:validate  # schema + catalog validation of examples/
```

## Automation

| Workflow | Trigger | Does |
|---|---|---|
| `.github/dependabot.yml` | daily (npm), weekly (GitHub Actions) | Opens PRs that bump the Microsoft packages / actions (both Microsoft packages in one grouped PR). |
| `update-catalog.yml` | Dependabot PRs, manual | `npm ci`, regenerates `catalog/`, commits it to the same PR. If the export breaks it fails with an annotation explaining that Microsoft probably changed an API/format. Manual runs on `main` open a PR. |
| `ci.yml` | PRs to `main` | Checks exact version pins, that `catalog/` is up to date, and that `examples/` validate against the PBIR schemas and the catalog (fails if a schema could not be downloaded). |

**One-time setup for fully automatic Dependabot PRs.** Commits pushed with the default `GITHUB_TOKEN` do not trigger
other workflows, so CI will not re-run on the bot's catalog commit. To fix that, create a fine-grained PAT (or GitHub App
token) with *Contents* and *Pull requests* write access and save it as `CATALOG_BOT_TOKEN` under both
**Settings -> Secrets -> Actions** and **Dependabot**. Without it everything still works, but you must re-run CI on those PRs.
Also require the `CI / verify` check in branch protection for `main`.

## Catalog format (v1)

```jsonc
{
  "visualType": "barChart",
  "deprecated": false,                 // + "alternative", "deprecationReason" when true
  "requiredRoles": ["Category", "Y"],
  "optionalRoles": ["Series", "Rows", "Tooltips"],
  "roles": { "Y": { "kind": "Measure", "displayName": "...", "required": true, "maxItems": null,
                    "requiredTypes": [{"numeric": true}, {"integer": true}] } },
  "roleCombinations": [ { "Rows": {"max": 0}, "Series": {"min": 1, "max": 1} } ],   // at least one must hold
  "formattingObjects": ["categoryAxis", "dataPoint", "legend", "..."],
  "sharedCapabilitiesWith": []
}
```

## License

MIT, see [LICENSE](LICENSE). Catalog data is derived from MIT-licensed Microsoft packages, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
