---
name: stock-news-analyzer
description: Analyze sourced news, SEC filings and earnings events for the WJ Top 300 US equities research repository. Use when implementing, reviewing or troubleshooting this workflow.
---

# stock-news-analyzer

## Purpose
Analyze sourced news, SEC filings and earnings events.

## Repository integration
Integrate opt-in news and SEC EDGAR adapters with honest provenance, timestamps, canonical URLs, deduplication and event-time cutoffs. SEC_USER_AGENT should identify the client. Distinguish source-reported facts from model interpretations; label unverified social sentiment and missing feeds. Do not invent headlines, citations, filings or event scores. Respect licensing and requests limits. Test missing news, delayed filings and ambiguous tickers.

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
