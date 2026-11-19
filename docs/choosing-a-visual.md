# Choosing a visual

> **Guidance, not generated data.** Unlike `catalog/`, this page is hand-written advice based on common data-visualization
> practice. It is not from Microsoft's packages. Every visual named here is checked against `catalog/` in CI
> (`scripts/check_docs.py`), so the names are valid, but whether a choice is *good* is a judgement call.

Start from what the user wants to **achieve**, not from a chart name. Then open `catalog/visuals/<type>.json`
(or `python3 scripts/visual_brief.py <type>`) to learn which roles to fill.

## 1. Pin down the goal first

Before choosing, know: **the question** the viewer should answer, **the audience** (executive glance vs analyst
exploration), and **the fields** available (how many categories, is there a date, is the measure a total, a ratio or a target comparison).
If the request is vague, ask, or state your assumption in one line.

## 2. Goal -> visual

| Goal | First choice | Alternatives | Avoid / watch out |
|---|---|---|---|
| Compare categories | `barChart` | `clusteredBarChart`, `columnChart`, `clusteredColumnChart` | Use horizontal bars for long labels; sort by value; don't use `pieChart` for this. |
| Trend over time | `lineChart` | `areaChart`, `stackedAreaChart` | Needs a real date/ordered axis; use a line, not columns, for many points. |
| Part of a whole | `donutChart` | `pieChart`, `treemap`, `hundredPercentStackedBarChart`, `hundredPercentStackedColumnChart` | Pie/donut only for ~2-5 slices that sum to a meaningful whole; use `treemap` for many categories. |
| Composition over time | `stackedAreaChart` | `hundredPercentStackedColumnChart`, `ribbonChart` | Too many series becomes unreadable; `ribbonChart` is for rank changes. |
| One headline number | `card` | `cardVisual`, `multiRowCard` (several numbers) | Add context (target, prior period) with `kpi` when a number alone is not meaningful. |
| Actual vs target / status | `kpi` | `gauge`, `scorecard` | `gauge` suits a single metric with a clear min/max/target; avoid many gauges on one page. |
| Bridge / what drove a change | `waterfallChart` | | Needs a start, steps and an end; not for unordered categories. |
| Funnel / stage drop-off | `funnel` | `barChart` | Stages must be ordered and shrinking. |
| Two measures over the same axis | `lineClusteredColumnComboChart` | | Dual axes can mislead; only combine measures with a clear relationship (e.g. revenue and margin %). |
| Relationship / correlation / outliers | `scatterChart` | `heatMap` | Needs two numeric measures; add `Size`/`Series` sparingly. |
| Exact values / lookup / detail | `tableEx` | `table` | A table is a last resort for patterns; keep columns few and formatted. |
| Cross-tab, totals, drill by rows and columns | `matrix` | `pivotTable` | Heavy on screen space; use for analyst pages. |
| Let the viewer filter | `slicer` | `listSlicer` | Few slicers, near the top or left, consistent across pages. |
| Geography | `azureMap` | | `map` and `filledMap` are deprecated: use `azureMap`. Needs location fields. |
| Why did it change / what drives it | `decompositionTreeVisual` | `keyDriversVisual` | Exploratory, interactive; not for static executive summaries. |
| Explain, label or navigate | `textbox` | `actionButton`, `pageNavigator` | Not data visuals; keep text short. |

## 3. Rules of thumb

- **One message per visual**; if a title needs "and", split it.
- **Fewer, larger visuals** beat many small ones. Roughly: key numbers on top, the main chart large, detail below.
- **Sort** categorical charts by value unless the order is natural (time, stages).
- **Limit categories**: more than ~7-10 bars or ~5 slices is a sign to filter, group, or switch visual.
- **Don't encode with colour alone**; keep the same colour for the same thing across the page.
- **Match field to role**: `Grouping` roles take columns, `Measure` roles take measures; respect `requiredTypes` in the catalog.

## 4. Then build it

1. Choose from the table, confirm it is `"deprecated": false` in the catalog.
2. Read its brief, fill the required roles, respect `maxItems` and `roleCombinations`.
3. Write `visual.json` (see `AGENTS.md`) and run `python3 scripts/validate_report.py <report>.Report`.
