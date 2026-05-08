#!/usr/bin/env python3
"""Walk-forward 5-fold evaluation for the Linear Regression baseline.

Time-series cross-validation using sklearn TimeSeriesSplit — the academic
standard for forecasting evaluation. Reports stability (mean ± std) of metrics
across 5 expanding-window folds, alongside the existing 70/30 and 80/20 single
splits in *_results.csv.

Output:
  results/linear_regression/linear_regression_walkforward.csv
      Per-fold rows: Ticker, Fold, Train_End, Test_Start, Test_End,
      RMSE, MAE, MAPE (%), R², Directional Accuracy (%)
  results/linear_regression/linear_regression_walkforward_summary.csv
      Per-ticker mean ± std across 5 folds.

Run:
  python scripts/walkforward_eval.py
"""

import logging
import sys
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.metrics import compute_metrics  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("walkforward")

FEATURED_DIR = ROOT / "data/processed/featured"
OUT_DIR = ROOT / "results/linear_regression"

TICKERS = ["VCB", "FPT", "HPG", "VIC", "VNM"]
N_SPLITS = 5
MODEL_NAME = "Linear Regression"

FEATURES = [
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


def evaluate_walkforward(ticker: str) -> list[dict]:
    src = FEATURED_DIR / f"{ticker}_featured.csv"
    if not src.exists():
        raise FileNotFoundError(
            f"Featured file not found: {src}. Run scripts/run_pipeline.py first."
        )
    df = pd.read_csv(src, parse_dates=["date"]).sort_values("date").reset_index(drop=True)

    # Predict close[t+1] from features[t].
    X_raw = df[FEATURES].iloc[:-1].values
    actual_now = df["close"].iloc[:-1].values
    actual_next = df["close"].iloc[1:].values
    dates_t = df["date"].iloc[:-1].values

    tscv = TimeSeriesSplit(n_splits=N_SPLITS)
    rows: list[dict] = []
    for fold, (tr_idx, te_idx) in enumerate(tscv.split(X_raw), 1):
        scaler = StandardScaler()
        X_tr = scaler.fit_transform(X_raw[tr_idx])
        X_te = scaler.transform(X_raw[te_idx])

        model = LinearRegression()
        model.fit(X_tr, actual_next[tr_idx])
        pred_next = model.predict(X_te)

        metrics = compute_metrics(
            y_true=actual_next[te_idx],
            y_pred=pred_next,
            prev_close=actual_now[te_idx],
        )

        rows.append(
            {
                "Ticker": ticker,
                "Split": "walkforward",
                "Model": MODEL_NAME,
                "Fold": fold,
                "Train_End": str(pd.Timestamp(dates_t[tr_idx[-1]]).date()),
                "Test_Start": str(pd.Timestamp(dates_t[te_idx[0]]).date()),
                "Test_End": str(pd.Timestamp(dates_t[te_idx[-1]]).date()),
                "Train_Rows": int(len(tr_idx)),
                "Test_Rows": int(len(te_idx)),
                **metrics,
            }
        )
        log.info(
            "  %s fold %d  test=[%s..%s] RMSE=%.3f DA=%.1f%%",
            ticker,
            fold,
            rows[-1]["Test_Start"],
            rows[-1]["Test_End"],
            metrics["RMSE"],
            metrics["Directional Accuracy (%)"],
        )
    return rows


def summarise(per_fold: pd.DataFrame) -> pd.DataFrame:
    metrics = ["RMSE", "MAE", "MAPE (%)", "R²", "Directional Accuracy (%)"]
    agg = per_fold.groupby(["Ticker", "Model"], as_index=False).agg(
        **{f"{m}_mean": (m, "mean") for m in metrics},
        **{f"{m}_std": (m, "std") for m in metrics},
        Folds=("Fold", "count"),
    )
    return agg.round(4)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    for ticker in TICKERS:
        log.info("Walk-forward (%d folds): %s", N_SPLITS, ticker)
        try:
            all_rows.extend(evaluate_walkforward(ticker))
        except Exception as exc:
            log.error("%s: walk-forward failed — %s", ticker, exc)

    if not all_rows:
        log.error("No results — check data/processed/featured/")
        sys.exit(1)

    per_fold = pd.DataFrame(all_rows)
    out_fold = OUT_DIR / "linear_regression_walkforward.csv"
    per_fold.to_csv(out_fold, index=False, encoding="utf-8-sig")
    log.info("Saved per-fold → %s", out_fold.relative_to(ROOT))

    summary = summarise(per_fold)
    out_sum = OUT_DIR / "linear_regression_walkforward_summary.csv"
    summary.to_csv(out_sum, index=False, encoding="utf-8-sig")
    log.info("Saved summary → %s", out_sum.relative_to(ROOT))

    print("\nSummary (mean ± std across 5 folds):")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
