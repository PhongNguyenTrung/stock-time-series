#!/usr/bin/env python3
"""Main pipeline: collect → preprocess → split → upload.

Usage:
  python scripts/run_pipeline.py                  # full run (Drive + Sheets if configured)
  python scripts/run_pipeline.py --skip-upload    # skip Google Drive rclone sync
  python scripts/run_pipeline.py --skip-sheets    # skip Google Sheets upload
  python scripts/run_pipeline.py --force          # re-download even if fresh
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# Allow imports from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collect import collect_all
from src.preprocess import preprocess_all
from src.split import split_all
from src.upload import upload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("pipeline")


def _step(name: str, fn, **kwargs):
    log.info("=" * 50)
    log.info("STEP: %s", name)
    log.info("=" * 50)
    t0 = time.time()
    result = fn(**kwargs)
    log.info("DONE: %s (%.1fs)", name, time.time() - t0)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Stock time series data pipeline")
    parser.add_argument(
        "--skip-upload", action="store_true", help="Skip Google Drive rclone upload"
    )
    parser.add_argument("--skip-sheets", action="store_true", help="Skip Google Sheets upload")
    parser.add_argument("--force", action="store_true", help="Force re-download of raw data")
    args = parser.parse_args()

    t_total = time.time()
    log.info("Pipeline started")

    try:
        collected = _step("1/4  collect", collect_all, force=args.force)
        preprocessed = _step("2/4  preprocess", preprocess_all)
        _step("3/4  split", split_all)

        if args.skip_upload:
            log.info("STEP: 4a/5  Drive upload — SKIPPED (--skip-upload)")
        else:
            ok = upload()
            if not ok:
                log.error("Drive upload failed — data may not be available to teammates")
                sys.exit(1)

        sheets_configured = bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
        if args.skip_sheets or not sheets_configured:
            reason = "--skip-sheets" if args.skip_sheets else "GOOGLE_SERVICE_ACCOUNT_JSON not set"
            log.info("STEP: 4b/5  Sheets upload — SKIPPED (%s)", reason)
        else:
            from src.sheets import upload_to_sheets

            ok = _step("4b/5  sheets", upload_to_sheets)
            if not ok:
                log.warning("Sheets upload failed — teammates may not see latest data")

    except Exception as exc:
        log.exception("Pipeline failed: %s", exc)
        sys.exit(1)

    # Warn if any tickers failed during collect / preprocess
    failed_collect = [t for t in ["VCB", "FPT", "HPG", "VIC", "VNM"] if t not in (collected or {})]
    if failed_collect:
        log.warning("Tickers not collected: %s", failed_collect)

    failed_pre = [t for t in ["VCB", "FPT", "HPG", "VIC", "VNM"] if t not in (preprocessed or {})]
    if failed_pre:
        log.warning("Tickers not preprocessed: %s", failed_pre)

    log.info("Pipeline complete in %.1fs", time.time() - t_total)


if __name__ == "__main__":
    main()
