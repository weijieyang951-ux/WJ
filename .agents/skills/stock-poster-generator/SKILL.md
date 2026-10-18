---
name: stock-poster-generator
description: Render 25 English mobile-friendly industry posters for the WJ Top 300 US equities research repository. Use when implementing, reviewing or troubleshooting this workflow.
---

# stock-poster-generator

## Purpose
Render 25 English mobile-friendly industry posters.

## Repository integration
Reuse research/render.py and config/themes.json plus config/settings.json. Generate exactly 25 English 1080x1920 PNG posters per successful run, each labeled with data date, sources, uncertainty and clear non-advice disclosure. Never add synthetic stocks to fill a theme; show no-coverage panels for empty themes. Use actual font metrics, ensure no clipping, save layout metadata, zip deliverables and test image dimensions, language and item counts. Preserve existing black_gold, navy and ivory templates.

## Workflow
1. Read README.md, ACCEPTANCE.md, config/settings.json and relevant research/ modules before editing.
2. Identify existing implementation and tests; extend rather than replace.
3. Keep mock and live outputs isolated, preserving reproducibility and source provenance.
4. Add unit and integration tests, run `pytest -q` and report failures honestly.
5. Record changed files, coverage gaps, licensing and operational blockers.

## Acceptance
- No invented market values, headlines, tickers, sources or probabilities.
- Errors are visible, machine-readable and never silently converted to success.
- Existing GitHub Actions and outputs remain compatible unless migration is explicitly reviewed.
- Do not modify secrets or enable trading.
