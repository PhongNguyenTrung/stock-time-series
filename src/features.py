"""Compute technical indicators — gold layer.

Single responsibility: take cleaned OHLCV (silver) and emit a feature-rich
DataFrame ready for modelling and splitting. Cleaning lives in
``src/clean.py`` — change feature definitions here without re-running cleanup.

Pipeline position:  collect (bronze) → clean (silver) → **features (gold)** → split

Indicators (all from the ``ta`` library):
  - MA   : ma_5, ma_20, ma_50
  - RSI  : rsi_14
  - MACD : macd, macd_signal, macd_hist (fast=12, slow=26, signal=9)
  - BB   : bb_upper, bb_middle, bb_lower (window=20, std=2)

Warm-up: drop the first 50 rows so that every indicator (largest window = MA50)
is fully populated.
"""

import logging
import os
from pathlib import Path

import pandas as pd
import ta
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

TICKERS: list[str] = os.getenv("TICKERS", "VCB,FPT,HPG,VIC,VNM").split(",")
CLEANED_DIR = Path("data/processed/cleaned")
FEATURED_DIR = Path("data/processed/featured")

WARMUP_ROWS = 50


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add MA, RSI, MACD, Bollinger Bands. Pure function — no I/O."""
    close = df["close"]

    df["ma_5"] = ta.trend.sma_indicator(close, window=5)
    df["ma_20"] = ta.trend.sma_indicator(close, window=20)
    df["ma_50"] = ta.trend.sma_indicator(close, window=50)

    df["rsi_14"] = ta.momentum.rsi(close, window=14)

    macd_obj = ta.trend.MACD(close, window_fast=12, window_slow=26, window_sign=9)
    df["macd"] = macd_obj.macd()
    df["macd_signal"] = macd_obj.macd_signal()
    df["macd_hist"] = macd_obj.macd_diff()

    bb_obj = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    df["bb_upper"] = bb_obj.bollinger_hband()
    df["bb_middle"] = bb_obj.bollinger_mavg()
    df["bb_lower"] = bb_obj.bollinger_lband()

    return df


def featurize_ticker(ticker: str) -> Path:
    src = CLEANED_DIR / f"{ticker}.csv"
    if not src.exists():
        raise FileNotFoundError(f"Cleaned file not found: {src}. Run src.clean.clean_all() first.")

    df = pd.read_csv(src, parse_dates=["date"])
    df = add_indicators(df)
    df = df.iloc[WARMUP_ROWS:].reset_index(drop=True)

    FEATURED_DIR.mkdir(parents=True, exist_ok=True)
    dest = FEATURED_DIR / f"{ticker}_featured.csv"
    df.to_csv(dest, index=False)
    log.info("%s: featured %d rows → %s", ticker, len(df), dest)
    return dest


def featurize_all() -> dict[str, Path]:
    results: dict[str, Path] = {}
    for ticker in TICKERS:
        try:
            results[ticker] = featurize_ticker(ticker)
        except Exception as exc:
            log.error("%s: featurization failed — %s", ticker, exc)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    featurize_all()
