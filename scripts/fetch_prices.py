#!/usr/bin/env python3
"""
fetch_prices.py

Stdlib-only price fetcher. Reads data/groups.json (company/ticker master list),
queries Yahoo Finance's public chart endpoint for each unique ticker, and writes
data/latest.json with the latest price, previous close, % change, and currency.

Design notes (matches tw-margin-table / tw-market-dashboard patterns):
- No third-party dependencies (no yfinance, no requests) -> nothing to pip install
  in GitHub Actions, fewer moving parts to break.
- Yahoo Finance requires a browser-like User-Agent or requests get rejected.
- Two-attempt fetch per ticker (retry once on transient network/SSL errors),
  small delay between requests to avoid being rate-limited.
- A ticker that fails after retries is recorded with price=None rather than
  crashing the whole run, so one bad symbol doesn't block the other ~124.

Run: python3 scripts/fetch_prices.py
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
GROUPS_PATH = ROOT / "data" / "groups.json"
OUTPUT_PATH = ROOT / "data" / "latest.json"

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

MAX_ATTEMPTS = 2
RETRY_DELAY_SEC = 2
REQUEST_DELAY_SEC = 0.6  # be polite between requests


def load_tickers():
    with open(GROUPS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    tickers = set()
    for group in data["groups"]:
        for company in group["companies"]:
            tickers.add(company["ticker"])
    return sorted(tickers)


def fetch_one(ticker: str):
    url = CHART_URL.format(ticker=ticker)
    last_err = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            result = payload.get("chart", {}).get("result")
            if not result:
                raise ValueError(f"empty chart result for {ticker}")
            meta = result[0]["meta"]
            price = meta.get("regularMarketPrice")
            prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
            currency = meta.get("currency")
            market_time = meta.get("regularMarketTime")
            change_pct = None
            if price is not None and prev_close:
                change_pct = round((price - prev_close) / prev_close * 100, 2)
            return {
                "ticker": ticker,
                "price": price,
                "prev_close": prev_close,
                "change_pct": change_pct,
                "currency": currency,
                "market_time": market_time,
                "ok": True,
            }
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError) as e:
            last_err = e
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY_SEC)
    return {
        "ticker": ticker,
        "price": None,
        "prev_close": None,
        "change_pct": None,
        "currency": None,
        "market_time": None,
        "ok": False,
        "error": str(last_err),
    }


def main():
    tickers = load_tickers()
    print(f"Fetching {len(tickers)} unique tickers...")

    results = {}
    failures = []
    for i, ticker in enumerate(tickers, 1):
        info = fetch_one(ticker)
        results[ticker] = info
        status = "OK" if info["ok"] else f"FAIL ({info.get('error')})"
        print(f"[{i}/{len(tickers)}] {ticker:14s} {status}")
        if not info["ok"]:
            failures.append(ticker)
        time.sleep(REQUEST_DELAY_SEC)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tickers": results,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(tickers) - len(failures)}/{len(tickers)} succeeded.")
    if failures:
        print("Failed tickers:", ", ".join(failures))


if __name__ == "__main__":
    main()
