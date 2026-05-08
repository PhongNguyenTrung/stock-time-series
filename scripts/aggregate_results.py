#!/usr/bin/env python3
"""Tổng hợp kết quả từ tất cả thành viên → bảng so sánh Chương 5.

Cách dùng:
  python scripts/aggregate_results.py               # tổng hợp + vẽ biểu đồ
  python scripts/aggregate_results.py --split 70_30 # chỉ 1 tỷ lệ split
  python scripts/aggregate_results.py --no-plot     # chỉ xuất bảng CSV/text

Quy ước CSV đầu vào (mỗi thành viên export ra):
  results/<tên_model>/<tên_model>_results.csv
  Cột bắt buộc: Ticker, Split, Model, RMSE, MAE, MAPE (%), R²

Đầu ra:
  results/comparison/chapter5_comparison.csv        ← bảng tổng hợp
  results/comparison/chapter5_pivot_rmse.csv        ← pivot RMSE
  results/comparison/chapter5_pivot_mae.csv         ← pivot MAE
  results/comparison/plots/                         ← biểu đồ so sánh
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("aggregate")

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / "results"
OUT_DIR = RESULTS_DIR / "comparison"
PLOTS_DIR = OUT_DIR / "plots"
REGISTRY_PATH = RESULTS_DIR / "registry.json"

TICKERS = ["VCB", "FPT", "HPG", "VIC", "VNM"]
CORE_METRICS = ["RMSE", "MAE", "MAPE (%)", "R²"]
OPTIONAL_METRICS = ["Directional Accuracy (%)"]
METRICS = CORE_METRICS  # plotting loop — kept for backward compat
REQUIRED_COLS = {"Ticker", "Split", "Model", "RMSE", "MAE", "MAPE (%)", "R²"}
WF_METRICS = CORE_METRICS + OPTIONAL_METRICS

COLORS = [
    "#2563EB",
    "#DC2626",
    "#16A34A",
    "#D97706",
    "#7C3AED",
    "#0891B2",
    "#BE185D",
]


# ── Helpers ────────────────────────────────────────────────────────────────


def collect_csvs() -> list[Path]:
    """Tìm tất cả *_results.csv trong results/ (bỏ qua thư mục eda và comparison).

    Loại trừ *_walkforward.csv — đã có collect_walkforward_csvs() riêng.
    """
    skip = {"eda", "comparison"}
    paths = []
    for p in sorted(RESULTS_DIR.rglob("*_results.csv")):
        if p.parts[len(RESULTS_DIR.parts)] not in skip:
            paths.append(p)
    return paths


def collect_walkforward_csvs() -> list[Path]:
    """Tìm tất cả *_walkforward.csv (per-fold output từ scripts/walkforward_eval.py)."""
    skip = {"eda", "comparison"}
    paths = []
    for p in sorted(RESULTS_DIR.rglob("*_walkforward.csv")):
        if p.name.endswith("_walkforward_summary.csv"):
            continue
        if p.parts[len(RESULTS_DIR.parts)] not in skip:
            paths.append(p)
    return paths


def load_all(csv_paths: list[Path]) -> pd.DataFrame:
    """Load và merge tất cả CSV kết quả, kiểm tra định dạng.

    Cột bắt buộc: REQUIRED_COLS. Cột tùy chọn (giữ nếu có, NaN nếu thiếu):
    OPTIONAL_METRICS — ví dụ "Directional Accuracy (%)".
    """
    frames = []
    for path in csv_paths:
        try:
            df = pd.read_csv(path)
            missing = REQUIRED_COLS - set(df.columns)
            if missing:
                log.warning("Bỏ qua %s — thiếu cột: %s", path.name, missing)
                continue
            keep = list(REQUIRED_COLS) + [c for c in OPTIONAL_METRICS if c in df.columns]
            sub = df[keep].copy()
            for m in OPTIONAL_METRICS:
                if m not in sub.columns:
                    sub[m] = np.nan
            frames.append(sub)
            extras = [c for c in OPTIONAL_METRICS if c in df.columns]
            log.info(
                "  Loaded: %s  (%d rows, models: %s%s)",
                path.name,
                len(df),
                df["Model"].unique().tolist(),
                f", +{extras}" if extras else "",
            )
        except Exception as exc:
            log.warning("Không đọc được %s: %s", path.name, exc)

    if not frames:
        log.error("Không tìm thấy CSV kết quả hợp lệ nào trong results/")
        sys.exit(1)

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["Ticker", "Split", "Model"])
    return combined


def load_walkforward(csv_paths: list[Path]) -> pd.DataFrame | None:
    """Load và gom các *_walkforward.csv (per-fold). Trả về None nếu không có."""
    if not csv_paths:
        return None
    frames: list[pd.DataFrame] = []
    for path in csv_paths:
        try:
            df = pd.read_csv(path)
            need = {"Ticker", "Model", "Fold", "RMSE", "MAE"}
            missing = need - set(df.columns)
            if missing:
                log.warning("Bỏ qua walk-forward %s — thiếu cột: %s", path.name, missing)
                continue
            for m in OPTIONAL_METRICS:
                if m not in df.columns:
                    df[m] = np.nan
            frames.append(df)
            log.info(
                "  Loaded walk-forward: %s  (%d rows × %d folds, models: %s)",
                path.name,
                len(df),
                df["Fold"].nunique(),
                df["Model"].unique().tolist(),
            )
        except Exception as exc:
            log.warning("Không đọc được %s: %s", path.name, exc)
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def summarise_walkforward(per_fold: pd.DataFrame) -> pd.DataFrame:
    """Mean ± std của metrics qua các fold, gom theo (Ticker, Model)."""
    metrics = [m for m in WF_METRICS if m in per_fold.columns]
    agg = per_fold.groupby(["Ticker", "Model"], as_index=False).agg(
        **{f"{m}_mean": (m, "mean") for m in metrics},
        **{f"{m}_std": (m, "std") for m in metrics},
        Folds=("Fold", "count"),
    )
    return agg.round(4)


def update_registry(df: pd.DataFrame) -> dict:
    """Cập nhật results/registry.json với champion mỗi (Ticker, Split).

    Champion = model RMSE thấp nhất. Mỗi lần aggregate chạy:
      - Nếu (Ticker, Split) chưa có champion → ghi "initial"
      - Nếu champion model thay đổi → ghi "promote"
      - Nếu cùng model nhưng RMSE đổi (retrain) → ghi "retrain"
      - Không thay đổi gì → bỏ qua
    """
    registry: dict = {"champions": {}, "history": []}
    if REGISTRY_PATH.exists():
        try:
            registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            registry.setdefault("champions", {})
            registry.setdefault("history", [])
        except Exception as exc:
            log.warning("registry.json không đọc được, tạo mới: %s", exc)

    timestamp = datetime.now().isoformat(timespec="seconds")
    best_idx = df.groupby(["Ticker", "Split"])["RMSE"].idxmin()
    new_champs = df.loc[best_idx]

    for _, row in new_champs.iterrows():
        key = f"{row['Ticker']}__{row['Split']}"
        entry = {
            "ticker": row["Ticker"],
            "split": row["Split"],
            "model": row["Model"],
            "rmse": float(row["RMSE"]),
            "mae": float(row["MAE"]),
            "since": timestamp,
        }
        da_col = "Directional Accuracy (%)"
        if da_col in row and pd.notna(row[da_col]):
            entry["directional_accuracy_pct"] = float(row[da_col])

        prev = registry["champions"].get(key)
        if prev is None:
            registry["champions"][key] = entry
            registry["history"].append(
                {
                    "timestamp": timestamp,
                    "ticker": row["Ticker"],
                    "split": row["Split"],
                    "event": "initial",
                    "model": row["Model"],
                    "rmse": float(row["RMSE"]),
                }
            )
        elif prev["model"] != row["Model"]:
            registry["champions"][key] = entry
            registry["history"].append(
                {
                    "timestamp": timestamp,
                    "ticker": row["Ticker"],
                    "split": row["Split"],
                    "event": "promote",
                    "from_model": prev["model"],
                    "to_model": row["Model"],
                    "rmse_improvement": round(prev["rmse"] - float(row["RMSE"]), 4),
                }
            )
        elif abs(prev.get("rmse", float("inf")) - float(row["RMSE"])) > 1e-6:
            registry["champions"][key] = {**entry, "since": prev.get("since", timestamp)}
            registry["history"].append(
                {
                    "timestamp": timestamp,
                    "ticker": row["Ticker"],
                    "split": row["Split"],
                    "event": "retrain",
                    "model": row["Model"],
                    "rmse": float(row["RMSE"]),
                    "previous_rmse": prev["rmse"],
                }
            )

    registry["updated_at"] = timestamp
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    return registry


def rank_models(df: pd.DataFrame) -> pd.DataFrame:
    """Thêm cột Rank_RMSE và Rank_MAE trong mỗi nhóm (Ticker, Split)."""
    df = df.copy()
    df["Rank_RMSE"] = df.groupby(["Ticker", "Split"])["RMSE"].rank(ascending=True).astype(int)
    df["Rank_MAE"] = df.groupby(["Ticker", "Split"])["MAE"].rank(ascending=True).astype(int)
    return df


# ── Bảng pivot ─────────────────────────────────────────────────────────────


def make_pivot(df: pd.DataFrame, metric: str, split: str) -> pd.DataFrame:
    """Pivot: hàng = Ticker, cột = Model, giá trị = metric."""
    sub = df[df["Split"] == split]
    pivot = sub.pivot_table(index="Ticker", columns="Model", values=metric)
    pivot.index.name = "Mã"
    pivot.columns.name = None
    return pivot.round(4)


# ── Visualisation ───────────────────────────────────────────────────────────


def plot_bar_comparison(df: pd.DataFrame, metric: str, split: str) -> None:
    """Bar chart: mỗi nhóm cột là 1 mã, mỗi cột là 1 model."""
    sub = df[df["Split"] == split].sort_values(["Ticker", "Model"])
    models = sorted(sub["Model"].unique())
    x = np.arange(len(TICKERS))
    width = 0.8 / max(len(models), 1)
    offsets = np.linspace(-(len(models) - 1) / 2, (len(models) - 1) / 2, len(models)) * width

    fig, ax = plt.subplots(figsize=(13, 5))
    for i, (model, color) in enumerate(zip(models, COLORS)):
        vals = []
        for ticker in TICKERS:
            row = sub[(sub["Ticker"] == ticker) & (sub["Model"] == model)]
            vals.append(row[metric].values[0] if not row.empty else np.nan)
        bars = ax.bar(x + offsets[i], vals, width=width * 0.9, label=model, color=color, alpha=0.85)
        # Label giá trị trên cột
        for bar, v in zip(bars, vals):
            if not np.isnan(v):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + bar.get_height() * 0.02,
                    f"{v:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=7.5,
                )

    ax.set_xticks(x)
    ax.set_xticklabels(TICKERS, fontsize=11)
    ax.set_ylabel(metric)
    ax.set_title(
        f"So sánh {metric} — Split {split.replace('_', '/')} "
        f"({'Thấp hơn = tốt hơn' if metric != 'R²' else 'Cao hơn = tốt hơn'})",
        pad=10,
    )
    ax.legend(loc="upper right", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax.grid(axis="y", ls=":", alpha=0.4)
    plt.tight_layout()

    fname = (
        PLOTS_DIR
        / f"comparison_{metric.lower().replace(' ', '_').replace('(', '').replace(')', '')}_{split}.png"
    )
    fig.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info("  Saved → %s", fname.relative_to(ROOT))


def plot_heatmap(df: pd.DataFrame, metric: str, split: str) -> None:
    """Heatmap pivot: model × ticker, màu = giá trị metric."""
    pivot = make_pivot(df, metric, split)
    reverse = metric == "R²"  # R²: màu tốt = cao

    fig, ax = plt.subplots(figsize=(max(8, len(pivot.columns) * 1.4), 4))
    import seaborn as sns

    sns.heatmap(
        pivot.T,
        annot=True,
        fmt=".3f",
        cmap="RdYlGn" if reverse else "RdYlGn_r",
        linewidths=0.5,
        ax=ax,
        cbar_kws={"label": metric, "shrink": 0.8},
    )
    ax.set_title(f"Heatmap {metric} — Split {split.replace('_', '/')}", pad=10)
    ax.set_xlabel("Mã cổ phiếu")
    ax.set_ylabel("Model")
    plt.tight_layout()

    fname = (
        PLOTS_DIR
        / f"heatmap_{metric.lower().replace(' ', '_').replace('(', '').replace(')', '')}_{split}.png"
    )
    fig.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info("  Saved → %s", fname.relative_to(ROOT))


def plot_rank_summary(df: pd.DataFrame, split: str) -> None:
    """Bar chart xếp hạng trung bình RMSE theo model."""
    sub = df[df["Split"] == split]
    avg_rank = sub.groupby("Model")["Rank_RMSE"].mean().sort_values().reset_index()

    fig, ax = plt.subplots(figsize=(max(6, len(avg_rank) * 1.2), 4))
    bars = ax.bar(
        avg_rank["Model"],
        avg_rank["Rank_RMSE"],
        color=COLORS[: len(avg_rank)],
        alpha=0.85,
        edgecolor="white",
    )
    for bar, v in zip(bars, avg_rank["Rank_RMSE"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.05,
            f"{v:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_ylabel("Xếp hạng RMSE trung bình (1 = tốt nhất)")
    ax.set_title(f"Xếp hạng trung bình theo RMSE — Split {split.replace('_', '/')}", pad=10)
    ax.set_ylim(0, len(sub["Model"].unique()) + 0.5)
    plt.xticks(rotation=20, ha="right")
    ax.grid(axis="y", ls=":", alpha=0.4)
    plt.tight_layout()

    fname = PLOTS_DIR / f"rank_summary_{split}.png"
    fig.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info("  Saved → %s", fname.relative_to(ROOT))


# ── Main ────────────────────────────────────────────────────────────────────


def print_section(title: str) -> None:
    log.info("─" * 55)
    log.info("  %s", title)
    log.info("─" * 55)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tổng hợp kết quả dự báo chuỗi thời gian")
    parser.add_argument(
        "--split",
        default=None,
        choices=["70_30", "80_20"],
        help="Chỉ xử lý 1 split (mặc định: cả hai)",
    )
    parser.add_argument("--no-plot", action="store_true", help="Bỏ qua bước vẽ biểu đồ")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Load ──
    print_section("1. Tìm và load CSV kết quả")
    csv_paths = collect_csvs()
    log.info("  Tìm thấy %d file:", len(csv_paths))
    for p in csv_paths:
        log.info("    %s", p.relative_to(ROOT))

    df = load_all(csv_paths)
    df = rank_models(df)

    splits = [args.split] if args.split else sorted(df["Split"].unique())
    models = sorted(df["Model"].unique())
    log.info("  Models: %s", models)
    log.info("  Splits: %s", splits)
    log.info("  Tổng: %d dòng", len(df))

    # ── 2. Bảng tổng hợp ──
    print_section("2. Bảng tổng hợp")
    rounding = {"RMSE": 2, "MAE": 2, "MAPE (%)": 3, "R²": 4}
    if "Directional Accuracy (%)" in df.columns:
        rounding["Directional Accuracy (%)"] = 2
    full_table = df.sort_values(["Split", "Ticker", "RMSE"]).round(rounding).reset_index(drop=True)
    out_csv = OUT_DIR / "chapter5_comparison.csv"
    full_table.to_csv(out_csv, index=False, encoding="utf-8-sig")
    log.info("  Saved → %s", out_csv.relative_to(ROOT))
    print(full_table.to_string(index=False))

    # ── 3. Pivot tables ──
    print_section("3. Pivot tables")
    for split in splits:
        for metric in ["RMSE", "MAE"]:
            pivot = make_pivot(df, metric, split)
            out = OUT_DIR / f"chapter5_pivot_{metric.lower()}_{split}.csv"
            pivot.to_csv(out, encoding="utf-8-sig")
            log.info("  Saved → %s", out.relative_to(ROOT))
            print(f"\n  {metric} — Split {split.replace('_', '/')}:")
            print(pivot.to_string())

    # ── 4. Biểu đồ ──
    if not args.no_plot:
        print_section("4. Vẽ biểu đồ so sánh")
        plt.rcParams.update({"figure.dpi": 120, "font.size": 10})

        for split in splits:
            for metric in METRICS:
                plot_bar_comparison(df, metric, split)
                plot_heatmap(df, metric, split)
            plot_rank_summary(df, split)

        log.info(
            "  Tổng %d biểu đồ → %s", len(list(PLOTS_DIR.iterdir())), PLOTS_DIR.relative_to(ROOT)
        )

    # ── 5. Tóm tắt kết quả tốt nhất ──
    print_section("5. Model tốt nhất theo RMSE (mỗi mã, mỗi split)")
    best_cols = ["Ticker", "Split", "Model", "RMSE", "MAE", "R²"]
    if "Directional Accuracy (%)" in df.columns:
        best_cols.append("Directional Accuracy (%)")
    best = (
        df.loc[df.groupby(["Ticker", "Split"])["RMSE"].idxmin()][best_cols]
        .sort_values(["Split", "Ticker"])
        .round({"RMSE": 2, "MAE": 2, "R²": 4, "Directional Accuracy (%)": 2})
        .reset_index(drop=True)
    )
    print(best.to_string(index=False))
    best.to_csv(OUT_DIR / "chapter5_best_models.csv", index=False, encoding="utf-8-sig")

    # ── 6. Walk-forward summary (nếu có) ──
    print_section("6. Walk-forward (5-fold TimeSeriesSplit)")
    wf_paths = collect_walkforward_csvs()
    if not wf_paths:
        log.info("  Không tìm thấy *_walkforward.csv — bỏ qua.")
        log.info("  (Chạy: python scripts/walkforward_eval.py để tạo cho Linear Regression)")
    else:
        wf = load_walkforward(wf_paths)
        if wf is not None and not wf.empty:
            wf_per_fold = OUT_DIR / "chapter5_walkforward_per_fold.csv"
            wf.to_csv(wf_per_fold, index=False, encoding="utf-8-sig")
            log.info("  Saved per-fold → %s", wf_per_fold.relative_to(ROOT))

            wf_summary = summarise_walkforward(wf)
            wf_sum_path = OUT_DIR / "chapter5_walkforward_summary.csv"
            wf_summary.to_csv(wf_sum_path, index=False, encoding="utf-8-sig")
            log.info("  Saved summary → %s", wf_sum_path.relative_to(ROOT))
            print(wf_summary.to_string(index=False))

    # ── 7. Model registry (champion / history) ──
    print_section("7. Model registry — champion theo RMSE")
    registry = update_registry(df)
    log.info("  Champions: %d entries", len(registry["champions"]))
    log.info("  History: %d events", len(registry["history"]))
    log.info("  Saved → %s", REGISTRY_PATH.relative_to(ROOT))
    for key, champ in sorted(registry["champions"].items()):
        da = champ.get("directional_accuracy_pct")
        da_str = f"  DA={da:.1f}%" if da is not None else ""
        log.info(
            "    %-20s → %-22s RMSE=%.3f%s",
            key,
            champ["model"],
            champ["rmse"],
            da_str,
        )

    log.info("─" * 55)
    log.info("  Hoàn thành. Kết quả tại: %s", OUT_DIR.relative_to(ROOT))


if __name__ == "__main__":
    main()
