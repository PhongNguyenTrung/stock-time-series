"""Forecasting metrics — single source of truth.

Use this from notebooks so every model in the project reports identical metric
definitions. Saves you from copy-pasting metric formulas across notebooks.

Example
-------
    from src.metrics import compute_metrics
    m = compute_metrics(y_true, y_pred, prev_close=close_prev_day)
    rows.append({"Ticker": "VCB", "Split": "70_30", "Model": "LSTM", **m})
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray, prev_close: np.ndarray) -> float:
    """Percent of test samples where predicted direction matches actual.

    Direction = sign(value - prev_close). Flat days (actual sign == 0) are
    excluded so they don't trivially inflate the score by matching 0 == 0.

    All three arrays must align: y_true[i], y_pred[i] are tomorrow's values
    and prev_close[i] is today's close.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    prev_close = np.asarray(prev_close)
    actual_dir = np.sign(y_true - prev_close)
    pred_dir = np.sign(y_pred - prev_close)
    mask = actual_dir != 0
    if mask.sum() == 0:
        return float("nan")
    return float((actual_dir[mask] == pred_dir[mask]).mean() * 100)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    prev_close: np.ndarray | None = None,
) -> dict[str, float]:
    """Return the full metric dict expected by aggregate_results.py.

    Keys: RMSE, MAE, MAPE (%), R², Directional Accuracy (%) (only if
    `prev_close` is provided).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    # Avoid divide-by-zero in MAPE — exclude rows where y_true == 0.
    nonzero = y_true != 0
    mape = (
        float(np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100)
        if nonzero.any()
        else float("nan")
    )
    r2 = float(r2_score(y_true, y_pred))

    out: dict[str, float] = {
        "RMSE": round(rmse, 4),
        "MAE": round(mae, 4),
        "MAPE (%)": round(mape, 4),
        "R²": round(r2, 4),
    }
    if prev_close is not None:
        da = directional_accuracy(y_true, y_pred, prev_close)
        out["Directional Accuracy (%)"] = round(da, 2) if not np.isnan(da) else float("nan")
    return out
