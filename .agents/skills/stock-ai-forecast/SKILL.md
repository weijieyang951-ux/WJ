---
name: stock-ai-forecast
description: Produce next-session conditional scenarios and risk assessments for the WJ Top 300 US equities research repository. Use when implementing, reviewing or troubleshooting this workflow.
---

# stock-ai-forecast

## Purpose
Produce next-session conditional scenarios and risk assessments.

## Repository integration
Use only point-in-time verified prices, indicators, filings and news. Output bullish, base and bearish conditional scenarios, catalysts, invalidation levels and explicit risks. Do not claim calibrated probabilities unless a separately validated, out-of-sample model exists; the current repository uses rule-based scenarios. Include forecast-as-of, next NYSE session and subsequent outcome resolution. Disclose survivor bias and transaction cost assumptions in backtests. No orders or trade execution.

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
