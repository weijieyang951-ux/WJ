---
name: technical-analysis
description: Compute auditable technical indicators for each stock for the WJ Top 300 US equities research repository. Use when implementing, reviewing or troubleshooting this workflow.
---

# technical-analysis

## Purpose
Compute auditable technical indicators for each stock.

## Repository integration
Use chronological adjusted OHLCV as appropriate and existing ta dependency. Calculate SMA 20/50/200, EMA, RSI 14, MACD 12/26/9, ATR 14, Bollinger 20/2, relative volume and support/resistance with explicit definitions. Require warmup and propagate nulls instead of guessing. Produce structured JSON with observation date, units and signal rationale. Unit-test edge cases and no-future-data behavior.

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
