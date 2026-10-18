# Codex Top 300 Skills Integration

Six repository-local Codex skills are installed in `.agents/skills/`.

## Skills
- stock-data-fetcher: market data quality and source provenance
- stock-screener: Top 300 ranking and eligibility
- technical-analysis: reproducible indicators
- stock-news-analyzer: sourced news, SEC filings and earnings
- stock-ai-forecast: conditional next-session scenarios
- stock-poster-generator: 25 English 1080x1920 posters

## Existing application
This branch deliberately leaves `research/`, `config/`, `pyproject.toml`, and `.github/workflows/daily-analysis.yml` untouched. These skills are Codex operating instructions; they do not activate new data vendors or probabilistic models by themselves.

## Verification
1. Open the repository in Codex and inspect the six skills.
2. Install Python 3.12 and project test extras: `pip install -e '.[test]'`.
3. Run `pytest -q`.
4. Run `python -m research.pipeline --provider mock --date 2026-10-16` and inspect the 300 research outputs and 25 posters.
5. Configure POLYGON_API_KEY and POLYGON_RPM in GitHub Actions, then manually run polygon smoke test. Do not enable production without API coverage and timing validation.

## Production cautions
The existing pipeline has not been certified against live market data; news, social and event coverage is incomplete. Do not label scenario rules as calibrated return probabilities. Keep secrets out of Git.
