# AGENTS.md - building correct Power BI (PBIR) visuals with this catalog

This repo is a machine-readable catalog of Power BI visual types, generated from Microsoft's official
packages. **Never guess a role name, a role limit or a formatting object: look it up here first.**

## Rules

1. Look the visual type up in `catalog/` before writing or editing any `visual.json`.
2. **Do not edit anything in `catalog/` by hand.** It is generated (`npm ci && npm run catalog:build`).
3. Role names are case-sensitive and are the keys of `visual.query.queryState`.
4. Do not use a visual with `"deprecated": true`; use its `alternative`.
5. Finish every task by running `python3 scripts/validate_report.py <path to *.Report>` and fixing all findings.

## How to look a visual up

1. **Find the type.** Read `catalog/index.json` (`visuals[]`: `visualType`, `requiredRoles`, `optionalRoles`,
   `deprecated`), or run `python3 scripts/visual_brief.py --list`. Pick the type that matches the request
   (e.g. ranking by category -> `barChart`/`clusteredBarChart`; single number -> `card`; filter -> `slicer`).
2. **Read its brief.** `python3 scripts/visual_brief.py barChart` prints roles, limits and allowed combinations;
   the full data is in `catalog/visuals/barChart.json`.
3. **Fill the roles** (`roles.<Role>` in the visual file):

   | Field | Meaning |
   |---|---|
   | `kind` | `Grouping` = a column (category), `Measure` = an aggregated/measure value. Put the matching kind of field in the role. |
   | `required` | `true` -> `queryState.<Role>` must contain at least one projection. |
   | `maxItems` | Maximum projections in this role (`null` = unlimited). |
   | `requiredTypes` | The field's data type must match one of these (e.g. `{"numeric": true}`). |
   | `preferredTypes` / `noDuplicates` | Soft hints / don't put the same field twice (only present where Microsoft defines them). |

4. **Check `roleCombinations`.** It is a list of alternatives; **at least one** must hold. Each alternative maps a
   role to `{min, max}` field counts (`"max": 0` = the role must be empty). Roles not mentioned in an
   alternative are unconstrained. Example: `barChart` with `Category`, `Y` and no `Series`/`Rows` satisfies the first alternative.
5. **Formatting.** `formattingObjects` lists the keys allowed under `visual.objects`. Shared container objects
   (title, background, border, ...) go under `visual.visualContainerObjects`. For property-level detail use
   Microsoft's CLI (installed by `npm ci`):
   `npx powerbi-report-author formatting list-objects barChart`, `... describe-object barChart legend`.
6. **Validate** (step 5 of the rules).

## visual.json skeleton

Copy the `$schema` version from `examples/minimal-report` so it matches the pinned toolchain.

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.13.0/schema.json",
  "name": "amount_by_region",
  "position": { "x": 380, "y": 40, "z": 2, "height": 640, "width": 860, "tabOrder": 2 },
  "visual": {
    "visualType": "barChart",
    "query": {
      "queryState": {
        "Category": { "projections": [ { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "Sales" } }, "Property": "Region" } },
                                          "queryRef": "Sales.Region", "nativeQueryRef": "Region", "active": true } ] },
        "Y":        { "projections": [ { "field": { "Aggregation": { "Expression": { "Column": { "Expression": { "SourceRef": { "Entity": "Sales" } }, "Property": "Amount" } }, "Function": 0 } },
                                          "queryRef": "Sum(Sales.Amount)", "nativeQueryRef": "Sum of Amount" } ] }
      }
    },
    "drillFilterOtherVisuals": true
  }
}
```

Field shapes (all validated against Microsoft's schema in this repo's example):

- Column: `{"Column": {"Expression": {"SourceRef": {"Entity": "<Table>"}}, "Property": "<Column>"}}`
- Measure: `{"Measure": {"Expression": {"SourceRef": {"Entity": "<Table>"}}, "Property": "<Measure>"}}`
- Aggregated column: `{"Aggregation": {"Expression": <Column>, "Function": 0}}` (`0` = Sum, as used in the example; check the
  `visualContainer` schema for the other function codes before using them).
- `queryRef` is `Table.Field` (or `Func(Table.Field)` for aggregations); `nativeQueryRef` is the display name.
- Entity/Property names must exist in the report's semantic model (`*.SemanticModel`, TMDL).

## Layout of a PBIR report

```
<Name>.pbip
<Name>.Report/definition/report.json
<Name>.Report/definition/pages/pages.json            (pageOrder, activePageName)
<Name>.Report/definition/pages/<pageId>/page.json
<Name>.Report/definition/pages/<pageId>/visuals/<visualName>/visual.json
```

`examples/minimal-report` is a complete working project. Create a new empty project with
`npx powerbi-report-author scaffold <dir> --name <Name>`. Use unique `name` values per visual; keep
`position` inside the page `width`/`height` and avoid overlapping visuals.

## Commands

| Task | Command |
|---|---|
| List visual types | `python3 scripts/visual_brief.py --list` |
| Brief for one type | `python3 scripts/visual_brief.py <visualType>` |
| Validate a report (schemas + catalog) | `python3 scripts/validate_report.py <report>.Report` |
| Validate offline (skips remote schemas; local only) | `python3 scripts/validate_report.py --offline <report>.Report` |
| Regenerate the catalog | `npm ci && npm run catalog:build` |
| Check the catalog is current | `npm run catalog:check` |

## Limits

- Roles/limits/combinations are Microsoft's published metadata at the pinned package versions
  (`catalog/index.json` -> `sources`). They describe what a visual accepts, not whether a chart is a good design.
- The catalog covers the 57 types the authoring CLI knows. `index.json -> skipped` lists capability keys that exist in the
  schema package but that the CLI rejects (currently `ganttChart`); do not generate those.
- The upstream CLI is a `0.x` public preview; formats may change between versions.
