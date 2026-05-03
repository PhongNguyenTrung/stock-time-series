"""Clean raw OHLCV data and compute technical indicators.

Indicators added (all from the `ta` library):
  - MA   : ma_5, ma_20, ma_50
  - RSI  : rsi_14
  - MACD : macd, macd_signal, macd_hist
  - BB   : bb_upper, bb_middle, bb_lower
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
RAW_DIR = Path("data/raw")
FEATURED_DIR = Path("data/processed/featured")

# Warm-up rows to discard so all indicators are fully populated
WARMUP_ROWS = 50


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    # Drop rows where close is missing — these are structural gaps, not fill-able
    df = df.dropna(subset=["close"])
    # Forward-fill minor gaps (≤3 consecutive trading days) for other OHLCV columns
    df[["open", "high", "low", "volume"]] = (
        df[["open", "high", "low", "volume"]].ffill(limit=3)
    )
    return df


def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"]
    high = df["high"]
    low = df["low"]

    # Moving Averages
    df["ma_5"] = ta.trend.sma_indicator(close, window=5)
    df["ma_20"] = ta.trend.sma_indicator(close, window=20)
    df["ma_50"] = ta.trend.sma_indicator(close, window=50)

    # RSI
    df["rsi_14"] = ta.momentum.rsi(close, window=14)

    # MACD (fast=12, slow=26, signal=9)
    macd_obj = ta.trend.MACD(close, window_fast=12, window_slow=26, window_sign=9)
    df["macd"] = macd_obj.macd()
    df["macd_signal"] = macd_obj.macd_signal()
    df["macd_hist"] = macd_obj.macd_diff()

    # Bollinger Bands (window=20, std=2)
    bb_obj = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    df["bb_upper"] = bb_obj.bollinger_hband()
    df["bb_middle"] = bb_obj.bollinger_mavg()
    df["bb_lower"] = bb_obj.bollinger_lband()

    return df


def preprocess_ticker(ticker: str) -> Path:
    src = RAW_DIR / f"{ticker}.csv"
    if not src.exists():
        raise FileNotFoundError(f"Raw file not found: {src}")

    df = pd.read_csv(src)
    df = _clean(df)
    df = _add_indicators(df)

    # Drop warm-up rows where indicators aren't stable yet
    df = df.iloc[WARMUP_ROWS:].reset_index(drop=True)

    FEATURED_DIR.mkdir(parents=True, exist_ok=True)
    dest = FEATURED_DIR / f"{ticker}_featured.csv"
    df.to_csv(dest, index=False)
    log.info("%s: preprocessed %d rows → %s", ticker, len(df), dest)
    return dest


def preprocess_all() -> dict[str, Path]:
    results = {}
    for ticker in TICKERS:
        try:
            results[ticker] = preprocess_ticker(ticker)
        except Exception as exc:
            log.error("%s: preprocessing failed — %s", ticker, exc)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    preprocess_all()
