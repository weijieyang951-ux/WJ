---
name: stock-screener
description: Rank an eligible US equity universe and retain top 300 for the WJ Top 300 US equities research repository. Use when implementing, reviewing or troubleshooting this workflow.
---

# stock-screener

## Purpose
Rank an eligible US equity universe and retain top 300.

## Repository integration
Reuse existing eligibility and ranking implementation. Restrict to active US common shares; exclude ETFs, warrants and other ineligible instruments. Normalize factors cross-sectionally: liquidity 25%, relative volume 20%, momentum and volatility 20%, news attention 15%, earnings and events 10%, technical signals 10%. Record factor coverage and redistributed weights, rankings, ties and historical rank changes. If fewer than 300 eligible names remain, fail explicitly rather than fabricate. Prevent look-ahead leakage.

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
