"""Time-based train/test split for featured stock data.

Produces two split ratios (70/30 and 80/20) for each ticker.
Splits are strictly chronological — no shuffling — to prevent data leakage.

Output layout:
  data/processed/splits/70_30/{TICKER}_train.csv
  data/processed/splits/70_30/{TICKER}_test.csv
  data/processed/splits/80_20/{TICKER}_train.csv
  data/processed/splits/80_20/{TICKER}_test.csv
  data/processed/splits/split_info.json   ← cut dates for teammates
"""

import json
import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

TICKERS: list[str] = os.getenv("TICKERS", "VCB,FPT,HPG,VIC,VNM").split(",")
FEATURED_DIR = Path("data/processed/featured")
SPLITS_DIR = Path("data/processed/splits")
RATIOS: dict[str, float] = {"70_30": 0.70, "80_20": 0.80}


def split_ticker(ticker: str) -> dict:
    src = FEATURED_DIR / f"{ticker}_featured.csv"
    if not src.exists():
        raise FileNotFoundError(f"Featured file not found: {src}")

    df = pd.read_csv(src, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    n = len(df)

    info: dict = {"ticker": ticker, "total_rows": n, "splits": {}}

    for label, ratio in RATIOS.items():
        cut = int(n * ratio)
        train = df.iloc[:cut].reset_index(drop=True)
        test = df.iloc[cut:].reset_index(drop=True)

        split_dir = SPLITS_DIR / label
        split_dir.mkdir(parents=True, exist_ok=True)

        train.to_csv(split_dir / f"{ticker}_train.csv", index=False)
        test.to_csv(split_dir / f"{ticker}_test.csv", index=False)

        cut_date = str(df.iloc[cut]["date"].date())
        info["splits"][label] = {
            "train_rows": len(train),
            "test_rows": len(test),
            "train_end": str(train["date"].iloc[-1].date()),
            "test_start": cut_date,
            "test_end": str(test["date"].iloc[-1].date()),
        }
        log.info(
            "%s [%s]: train=%d rows (→%s) | test=%d rows (%s→)",
            ticker,
            label,
            len(train),
            info["splits"][label]["train_end"],
            len(test),
            cut_date,
        )

    return info


def split_all() -> None:
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    all_info: list[dict] = []

    for ticker in TICKERS:
        try:
            all_info.append(split_ticker(ticker))
        except Exception as exc:
            log.error("%s: split failed — %s", ticker, exc)

    info_path = SPLITS_DIR / "split_info.json"
    info_path.write_text(json.dumps(all_info, indent=2, ensure_ascii=False))
    log.info("Split info saved → %s", info_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    split_all()
