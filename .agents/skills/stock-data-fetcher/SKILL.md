---
name: stock-data-fetcher
description: Retrieve and validate daily US equity market data for the WJ Top 300 US equities research repository. Use when implementing, reviewing or troubleshooting this workflow.
---

# stock-data-fetcher

## Purpose
Retrieve and validate daily US equity market data.

## Repository integration
Use existing research provider adapters. Inspect research/pipeline.py and provider modules before changes. Keep Polygon and mock modes separate. Validate OHLCV chronology, positive prices, volumes, session calendar, symbol identity, splits, staleness and vendor permissions. Persist raw-source timestamps and explicit missing fields. Never substitute mock values for live values. Respect POLYGON_RPM and rate limits. Add deterministic tests for duplicates, gaps and missing feeds.

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
