"""Download OHLCV data for Vietnamese stocks.

Primary source: vnstock (HOSE/HNX data)
Fallback:       yfinance (ticker.VN suffix)
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

TICKERS: list[str] = os.getenv("TICKERS", "VCB,FPT,HPG,VIC,VNM").split(",")
START_DATE: str = os.getenv("START_DATE", "2016-01-01")
END_DATE: str = os.getenv("END_DATE", datetime.today().strftime("%Y-%m-%d"))
RAW_DIR = Path("data/raw")
FRESHNESS_HOURS = 24

COLUMN_MAP = {
    "time": "date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
}


def _is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age < timedelta(hours=FRESHNESS_HOURS)


def _fetch_vnstock(ticker: str) -> pd.DataFrame | None:
    try:
        from vnstock.api.quote import Quote

        q = Quote(symbol=ticker, source="VCI")
        df = q.history(start=START_DATE, end=END_DATE, interval="1D")
        df = df.rename(columns=str.lower)
        if "time" in df.columns:
            df = df.rename(columns={"time": "date"})
        df["date"] = pd.to_datetime(df["date"])
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception as exc:
        log.warning("vnstock failed for %s: %s", ticker, exc)
        return None


def _fetch_yfinance(ticker: str) -> pd.DataFrame | None:
    try:
        import yfinance as yf

        symbol = f"{ticker}.VN"
        raw = yf.download(symbol, start=START_DATE, end=END_DATE, progress=False)
        if raw.empty:
            log.warning("yfinance returned empty data for %s", symbol)
            return None
        raw = raw.reset_index()
        # yfinance may return MultiIndex columns
        raw.columns = [c[0] if isinstance(c, tuple) else c for c in raw.columns]
        raw.columns = [c.lower() for c in raw.columns]
        raw = raw.rename(columns={"adj close": "close", "date": "date"})
        raw["date"] = pd.to_datetime(raw["date"])
        return raw[["date", "open", "high", "low", "close", "volume"]]
    except Exception as exc:
        log.warning("yfinance failed for %s: %s", ticker, exc)
        return None


def collect_ticker(ticker: str, force: bool = False) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / f"{ticker}.csv"

    if not force and _is_fresh(dest):
        log.info("%s: skipped (fresh)", ticker)
        return dest

    log.info("%s: fetching from vnstock...", ticker)
    df = _fetch_vnstock(ticker)

    if df is None:
        log.info("%s: falling back to yfinance...", ticker)
        df = _fetch_yfinance(ticker)

    if df is None or df.empty:
        raise RuntimeError(f"No data retrieved for {ticker}")

    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    df.to_csv(dest, index=False)
    log.info("%s: saved %d rows → %s", ticker, len(df), dest)
    return dest


def collect_all(force: bool = False) -> dict[str, Path]:
    results = {}
    for ticker in TICKERS:
        try:
            results[ticker] = collect_ticker(ticker, force=force)
        except Exception as exc:
            log.error("%s: collection failed — %s", ticker, exc)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    collect_all()
