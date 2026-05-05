"""Upload processed data to Google Sheets via a service account.

Setup (one-time):
  1. Google Cloud Console → IAM → Service Accounts → create one
  2. Enable the Google Sheets API and Google Drive API
  3. Download the JSON key
  4. Share the target spreadsheet with the service account email
  5. Store the JSON key content as GitHub secret GOOGLE_SERVICE_ACCOUNT_JSON

.env variables (optional — also supports the GitHub secret path below):
  GOOGLE_SERVICE_ACCOUNT_JSON  absolute path to the JSON key file
  SHEETS_SPREADSHEET_ID        ID from the spreadsheet URL (after /d/)

Sheet structure written:
  - One tab per ticker (VCB, FPT, HPG, VIC, VNM) — full featured data
  - Tab "split_info"  — cut dates summary for teammates
  - Tab "README"      — column descriptions
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

_README_ROWS = [
    ["Column", "Description"],
    ["date", "Trading date (YYYY-MM-DD)"],
    ["open", "Opening price (VND)"],
    ["high", "Intraday high (VND)"],
    ["low", "Intraday low (VND)"],
    ["close", "Closing price (VND) — prediction target"],
    ["volume", "Trading volume (shares)"],
    ["ma_5", "Simple Moving Average, 5-day window"],
    ["ma_20", "Simple Moving Average, 20-day window"],
    ["ma_50", "Simple Moving Average, 50-day window"],
    ["rsi_14", "Relative Strength Index, 14-day window (0–100)"],
    ["macd", "MACD line (EMA12 − EMA26)"],
    ["macd_signal", "MACD signal line (EMA9 of MACD)"],
    ["macd_hist", "MACD histogram (macd − macd_signal)"],
    ["bb_upper", "Bollinger Band upper (MA20 + 2σ)"],
    ["bb_middle", "Bollinger Band middle (MA20)"],
    ["bb_lower", "Bollinger Band lower (MA20 − 2σ)"],
    [],
    ["Split boundaries", ""],
    ["70/30 train end", "2023-02-20  |  test start: 2023-02-21"],
    ["80/20 train end", "2024-03-12  |  test start: 2024-03-13"],
]


def _get_client():
    """Return an authenticated gspread client using service account credentials."""
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
    ]

    # Accept either a file path or raw JSON content (for GitHub Actions env var)
    sa_value = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not sa_value:
        raise EnvironmentError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is not set. "
            "Set it to the path of your service account JSON file "
            "or its contents as a JSON string."
        )

    if sa_value.strip().startswith("{"):
        info = json.loads(sa_value)
        creds = Credentials.from_service_account_info(info, scopes=scopes)
    else:
        creds = Credentials.from_service_account_file(sa_value, scopes=scopes)

    return gspread.authorize(creds)


def _upsert_sheet(spreadsheet, title: str) -> object:
    """Return existing worksheet or create a new one."""
    try:
        return spreadsheet.worksheet(title)
    except Exception:
        return spreadsheet.add_worksheet(title=title, rows=3000, cols=20)


def _write_df(ws, df: pd.DataFrame) -> None:
    """Write a DataFrame to a worksheet (header + rows)."""
    df = df.copy()
    df["date"] = df["date"].astype(str)
    # Round floats to 4 decimal places to keep cell size small
    float_cols = df.select_dtypes("float64").columns
    df[float_cols] = df[float_cols].round(4)

    data = [df.columns.tolist()] + df.fillna("").values.tolist()
    ws.clear()
    ws.update(data, value_input_option="RAW")


def upload_to_sheets(spreadsheet_id: str | None = None) -> bool:
    spreadsheet_id = spreadsheet_id or os.getenv("SHEETS_SPREADSHEET_ID", "")
    if not spreadsheet_id:
        log.error(
            "SHEETS_SPREADSHEET_ID not set. "
            "Create a Google Sheet and paste its ID into .env or the GitHub secret."
        )
        return False

    try:
        gc = _get_client()
        spreadsheet = gc.open_by_key(spreadsheet_id)
        log.info("Opened spreadsheet: %s", spreadsheet.title)
    except Exception as exc:
        log.error("Cannot open spreadsheet %s: %s", spreadsheet_id, exc)
        return False

    # ── Ticker tabs ───────────────────────────────────────────────────────
    for ticker in TICKERS:
        src = FEATURED_DIR / f"{ticker}_featured.csv"
        if not src.exists():
            log.warning("%s: featured file not found, skipping", ticker)
            continue
        df = pd.read_csv(src)
        ws = _upsert_sheet(spreadsheet, ticker)
        _write_df(ws, df)
        log.info("%s: wrote %d rows to sheet '%s'", ticker, len(df), ticker)

    # ── split_info tab ────────────────────────────────────────────────────
    info_path = SPLITS_DIR / "split_info.json"
    if info_path.exists():
        raw = json.loads(info_path.read_text())
        rows = []
        for entry in raw:
            for label, s in entry["splits"].items():
                rows.append(
                    {
                        "ticker": entry["ticker"],
                        "split": label,
                        "total_rows": entry["total_rows"],
                        "train_rows": s["train_rows"],
                        "test_rows": s["test_rows"],
                        "train_end": s["train_end"],
                        "test_start": s["test_start"],
                        "test_end": s["test_end"],
                    }
                )
        df_info = pd.DataFrame(rows)
        ws_info = _upsert_sheet(spreadsheet, "split_info")
        data = [df_info.columns.tolist()] + df_info.values.tolist()
        ws_info.clear()
        ws_info.update(data, value_input_option="RAW")
        log.info("split_info tab written (%d rows)", len(df_info))

    # ── README tab ────────────────────────────────────────────────────────
    ws_readme = _upsert_sheet(spreadsheet, "README")
    ws_readme.clear()
    ws_readme.update(_README_ROWS, value_input_option="RAW")
    log.info("README tab written")

    log.info(
        "Sheets upload complete → https://docs.google.com/spreadsheets/d/%s",
        spreadsheet_id,
    )
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    upload_to_sheets()
