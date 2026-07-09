# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A cross-market industry-linkage dashboard (台美日韓產業關聯儀表板) for observing how same-industry stocks move together across US/Taiwan/Japan/Korea markets. Static site deployed to GitHub Pages; UI text and data are in Traditional Chinese.

## Commands

There is no build step, no lint, and no tests.

- **Fetch prices**: `python3 scripts/fetch_prices.py` (Windows: `py scripts/fetch_prices.py`) — reads `data/groups.json`, queries Yahoo Finance, writes `data/latest.json`. Note: local networks with allowlists may not reach `query1.finance.yahoo.com`; it works in GitHub Actions.
- **Preview locally**: serve over HTTP, since `index.html` fetches `data/*.json` and that fails over `file://`. `.claude/launch.json` defines a `static-site` server (`py -m http.server 8000`).

## Architecture

Three moving parts, connected only through the two JSON files in `data/`:

1. `data/groups.json` — hand-maintained master file: industry groups → companies with `name`, `ticker`, `market` (US/TW/JP/KR), `product`, `source`. To add a company, edit this file only; the fetch script and UI pick it up automatically.
2. `scripts/fetch_prices.py` — **stdlib-only** Python (deliberate constraint: no pip installs in CI; do not add third-party dependencies). Fetches each unique ticker from Yahoo Finance's chart API with retry + rate-limit delay; a failing ticker is recorded with `price: null` rather than aborting the run. Writes `data/latest.json` (never hand-edit that file): `{generated_at, tickers: {<ticker>: {price, prev_close, change_pct, currency, market_time, ok}}}`.
3. `index.html` — the entire dashboard: vanilla HTML/CSS/JS in one file, no framework. Loads both JSON files at runtime and renders grouped tables with search and market filtering. It tolerates a missing/empty `latest.json` (shows a "waiting for first update" state), and per-ticker `null` prices render as `—`.

`.github/workflows/update.yml` runs daily (23:00 UTC = 07:00 Taipei): the `update-data` job fetches prices and commits `data/latest.json`, then `deploy-pages` re-checks out `main` (so it includes that commit) and deploys the repo root to GitHub Pages. Manual runs via workflow_dispatch. The 07:00 Taipei timing means each snapshot holds the just-finished US close alongside TW/JP/KR's previous-day closes — the `change_pct` values across markets are one trading day apart by design.

## Conventions

- Ticker format is Yahoo Finance's: US bare (`NVDA`), Taiwan listed `.TW`, Taiwan OTC `.TWO`, Japan `.T`, Korea `.KS`. Each company's `market` field must match its ticker suffix.
- The UI uses the Taiwanese color convention: **red = up, green = down** (`--up`/`--down` CSS variables).
- The visual design deliberately follows the Monocle-magazine editorial recipe (`.claude/skills/web-design-engineer/references/style-recipes/monocle-magazine.md`): cream paper background, Noto Serif TC, editorial red `#C7322E` doubling as "up", olive `#5E6347` as "down", hairline rules, zero border-radius, zero shadows. Keep new UI in this vocabulary; alternative design mockups live in `design-proposals/`.
- Industry groups are curated cross-market picks (3–8 companies each), not full index constituents — keep groups small and focused on Taiwan-market linkage.
