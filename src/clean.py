"""Clean raw OHLCV data — silver layer.

Single responsibility: take raw daily quotes and produce a clean, deduplicated,
sorted DataFrame. No feature engineering happens here — that lives in
``src/features.py``. Splitting the two means a feature change does not
re-trigger the cleaning step (and vice versa) and makes it obvious which
layer to inspect when results look wrong.

Pipeline position:  collect (bronze) → **clean (silver)** → features (gold) → split

Cleaning rules:
  - Drop rows where ``close`` is missing (structural gap, can't fill).
  - Forward-fill OHL + volume up to 3 calendar days (covers a long weekend).
    Note: ``volume`` ffill produces a synthetic value — acceptable here because
    the gap is short, but be aware in EDA.
  - Sort by date and drop duplicate dates.
"""

import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

TICKERS: list[str] = os.getenv("TICKERS", "VCB,FPT,HPG,VIC,VNM").split(",")
RAW_DIR = Path("data/raw")
CLEANED_DIR = Path("data/processed/cleaned")


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned copy of an OHLCV DataFrame. Pure function — no I/O."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    df = df.dropna(subset=["close"])
    df[["open", "high", "low", "volume"]] = df[["open", "high", "low", "volume"]].ffill(limit=3)
    return df


def clean_ticker(ticker: str) -> Path:
    src = RAW_DIR / f"{ticker}.csv"
    if not src.exists():
        raise FileNotFoundError(f"Raw file not found: {src}")

    df = pd.read_csv(src)
    df = clean_frame(df)

    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    dest = CLEANED_DIR / f"{ticker}.csv"
    df.to_csv(dest, index=False)
    log.info("%s: cleaned %d rows → %s", ticker, len(df), dest)
    return dest


def clean_all() -> dict[str, Path]:
    results: dict[str, Path] = {}
    for ticker in TICKERS:
        try:
            results[ticker] = clean_ticker(ticker)
        except Exception as exc:
            log.error("%s: cleaning failed — %s", ticker, exc)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    clean_all()
