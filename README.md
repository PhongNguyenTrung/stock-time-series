# Stock Time Series

Data pipeline for Vietnamese stock market forecasting research — **Member 1: Data Engineer**.

Collects, preprocesses, and splits historical price data for 5 tickers (VCB, FPT, HPG, VIC, VNM) to serve as shared input for the group's models (ARIMA, SVR, LSTM, GRU, Prophet, XGBoost).

---

## Project Structure

```
stock-time-series/
├── src/
│   ├── collect.py       # Download raw OHLCV data via vnstock/yfinance
│   ├── preprocess.py    # Clean data + feature engineering (MA, RSI, MACD, Bollinger Bands)
│   ├── split.py         # Train/test split (70/30 and 80/20)
│   └── upload.py        # Upload processed data to Google Drive via rclone
├── scripts/
│   └── run_pipeline.py  # Full pipeline runner
├── data/
│   ├── raw/             # Downloaded CSVs (git-ignored)
│   └── processed/       # Featured + split datasets (git-ignored)
├── .env.example         # Environment variable template
└── pyproject.toml
```

## Setup

**1. Clone & create virtual environment**

```bash
git clone https://github.com/PhongNguyenTrung/stock-time-series.git
cd stock-time-series
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

**2. Configure environment**

```bash
cp .env.example .env
# Edit .env with your settings (tickers, date range, rclone remote)
```

**3. (Optional) Configure rclone for Google Drive upload**

```bash
rclone config   # name the remote "gdrive"
```

## Usage

```bash
# Full pipeline: collect → preprocess → split → upload
python scripts/run_pipeline.py

# Skip upload (offline / dry-run)
python scripts/run_pipeline.py --skip-upload

# Force re-download raw data
python scripts/run_pipeline.py --force
```

## Output

| Path | Description |
|------|-------------|
| `data/raw/<TICKER>.csv` | Raw OHLCV data |
| `data/processed/featured/<TICKER>_featured.csv` | Cleaned + feature-engineered |
| `data/processed/splits/70_30/` | 70% train / 30% test |
| `data/processed/splits/80_20/` | 80% train / 20% test |

## Tech Stack

- **Data**: [vnstock](https://github.com/thinh-vu/vnstock), yfinance
- **Feature Engineering**: [ta](https://github.com/bukosabino/ta) (MA, RSI, MACD, Bollinger Bands)
- **Upload**: rclone → Google Drive
- **Python**: 3.11+
