# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Regenerations of `catalog/` caused by
Dependabot bumps are recorded in the git history (`chore(catalog): ...`) and in
`catalog/index.json` (`sources`), not repeated here unless the catalog *format* changes.

## [Unreleased]

## [0.1.0] - 2026-11-19

### Added
- `catalog/visuals/<visualType>.json` for all 57 visual types and `catalog/index.json`
  (source package versions, generation timestamp, skipped capability keys), generated from
  `@microsoft/powerbi-report-authoring-cli` 0.5.0 and `@microsoft/powerbi-core-visual-schema` 0.1.3.
- `scripts/export_visual_catalog.py`, `check_catalog.py`, `validate_report.py`, `visual_brief.py`, `check_pins.py`.
- `examples/minimal-report`: minimal PBIP project (card, slicer, bar chart) validated in CI.
- GitHub Actions: CI, automatic catalog regeneration for Dependabot PRs; Dependabot for npm (daily) and GitHub Actions (weekly).
- `README.md`, `AGENTS.md`, `CLAUDE.md`, Copilot instructions, `LICENSE`, `THIRD_PARTY_NOTICES.md`.
