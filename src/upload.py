"""Sync processed data to Google Drive using rclone.

Prerequisites:
  brew install rclone
  rclone config   # create a remote named "gdrive" pointing to Google Drive

.env variables:
  RCLONE_REMOTE=gdrive
  GDRIVE_FOLDER=stock-time-series/data
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

REMOTE = os.getenv("RCLONE_REMOTE", "gdrive")
GDRIVE_FOLDER = os.getenv("GDRIVE_FOLDER", "stock-time-series/data")
LOCAL_DIR = Path("data/processed/splits")


def _check_rclone() -> bool:
    return shutil.which("rclone") is not None


def upload() -> bool:
    if not _check_rclone():
        log.error("rclone not found. Install with: brew install rclone")
        return False

    if not LOCAL_DIR.exists():
        log.error("Splits directory not found: %s — run split step first", LOCAL_DIR)
        return False

    destination = f"{REMOTE}:{GDRIVE_FOLDER}/splits"
    cmd = [
        "rclone", "sync",
        str(LOCAL_DIR),
        destination,
        "--progress",
        "--transfers", "4",
    ]

    log.info("Syncing %s → %s", LOCAL_DIR, destination)
    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode != 0:
        log.error("rclone sync failed (exit %d)", result.returncode)
        return False

    log.info("Upload complete → %s", destination)
    log.info("Share this Drive folder with teammates: %s:%s", REMOTE, GDRIVE_FOLDER)
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    upload()
