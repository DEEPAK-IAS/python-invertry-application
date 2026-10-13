from __future__ import annotations
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

# --- App Settings ---
APP_NAME    = os.getenv("APP_NAME", "Dindigul School Point")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG       = os.getenv("DEBUG", "False").lower() == "true"

# --- All folders inside C:\StockManager\ ---
APP_DIR      = r"C:\StockManager"
DB_FILE_PATH = os.path.join(APP_DIR, "stock_manager.db")
DATABASE_URL = f"sqlite:///{DB_FILE_PATH}"   # always absolute, never relative

BACKUP_DIR   = os.path.join(APP_DIR, "backups")
REPORTS_DIR  = os.path.join(APP_DIR, "reports")
CACHE_DIR    = os.path.join(APP_DIR, "cache")
LOGS_DIR     = os.path.join(APP_DIR, "logs")

# Create all folders on first run (works both dev and installed exe)
for folder in [APP_DIR, BACKUP_DIR, REPORTS_DIR, CACHE_DIR, LOGS_DIR]:
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception:
        pass




