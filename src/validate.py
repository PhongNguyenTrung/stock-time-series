#!/usr/bin/env python3
"""Validate processed splits — fail-fast before data hits production.

Runs after split.py, exits non-zero on ANY check failure to block downstream
steps (Sheets upload, Pages publish). Catches issues like:
  - VIC stock split → close = 0
  - yfinance schema drift dropping a column
  - collect step skipped a ticker silently
  - indicator bug producing NaN explosion

Run:
  python scripts/validate.py
"""

import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("validate")

TICKERS: list[str] = os.getenv("TICKERS", "VCB,FPT,HPG,VIC,VNM").split(",")
SPLITS_DIR = Path("data/processed/splits")
RATIOS = ["70_30", "80_20"]

MIN_TRAIN_ROWS = 500
MIN_TEST_ROWS = 100
MAX_NULL_RATIO = 0.05  # 5% per indicator column

REQUIRED_COLS = [
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "ma_5",
    "ma_20",
    "ma_50",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_hist",
    "bb_upper",
    "bb_middle",
    "bb_lower",
]
INDICATOR_COLS = [
    "ma_5",
    "ma_20",
    "ma_50",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_hist",
    "bb_upper",
    "bb_middle",
    "bb_lower",
]


def _check_one(path: Path, label: str, min_rows: int, ticker: str, ratio: str) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"{ticker}/{ratio}/{label}: file not found"]
    df = pd.read_csv(path, parse_dates=["date"])

    missing = set(REQUIRED_COLS) - set(df.columns)
    if missing:
        errors.append(f"{ticker}/{ratio}/{label}: missing columns {sorted(missing)}")
        return errors  # bail early, other checks assume schema

    if len(df) < min_rows:
        errors.append(f"{ticker}/{ratio}/{label}: only {len(df)} rows (min {min_rows})")
    if (df["close"] <= 0).any():
        n = int((df["close"] <= 0).sum())
        errors.append(f"{ticker}/{ratio}/{label}: {n} rows with close <= 0")
    if not df["date"].is_monotonic_increasing:
        errors.append(f"{ticker}/{ratio}/{label}: dates not monotonically increasing")
    if df["date"].duplicated().any():
        n = int(df["date"].duplicated().sum())
        errors.append(f"{ticker}/{ratio}/{label}: {n} duplicate dates")

    for col in INDICATOR_COLS:
        null_ratio = df[col].isna().mean()
        if null_ratio > MAX_NULL_RATIO:
            errors.append(
                f"{ticker}/{ratio}/{label}: {col} has {null_ratio:.1%} nulls (max {MAX_NULL_RATIO:.0%})"
            )
    return errors


def check_split(ticker: str, ratio: str) -> list[str]:
    """Return list of error messages for one (ticker, split) pair."""
    base = SPLITS_DIR / ratio
    train_path = base / f"{ticker}_train.csv"
    test_path = base / f"{ticker}_test.csv"

    errors: list[str] = []
    errors.extend(_check_one(train_path, "train", MIN_TRAIN_ROWS, ticker, ratio))
    errors.extend(_check_one(test_path, "test", MIN_TEST_ROWS, ticker, ratio))

    # Cross-file: train_end must precede test_start (no leakage).
    if train_path.exists() and test_path.exists():
        try:
            train_df = pd.read_csv(train_path, parse_dates=["date"])
            test_df = pd.read_csv(test_path, parse_dates=["date"])
            if not train_df.empty and not test_df.empty:
                if train_df["date"].max() >= test_df["date"].min():
                    errors.append(
                        f"{ticker}/{ratio}: train_end ({train_df['date'].max().date()}) "
                        f">= test_start ({test_df['date'].min().date()}) — leakage risk"
                    )
        except Exception as exc:
            errors.append(f"{ticker}/{ratio}: cross-check failed — {exc}")
    return errors


def validate_all() -> int:
    all_errors: list[str] = []
    log.info("Validating %d tickers × %d splits...", len(TICKERS), len(RATIOS))
    for ticker in TICKERS:
        for ratio in RATIOS:
            errs = check_split(ticker, ratio)
            for e in errs:
                log.error("  FAIL: %s", e)
            all_errors.extend(errs)

    total = len(TICKERS) * len(RATIOS)
    if all_errors:
        log.error(
            "Validation FAILED: %d errors across %d combos — aborting pipeline",
            len(all_errors),
            total,
        )
        return 1
    log.info("Validation OK: %d ticker × split combos passed all checks.", total)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sys.exit(validate_all())
