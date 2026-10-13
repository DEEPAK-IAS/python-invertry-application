from __future__ import annotations
import sys
import os
from loguru import logger

def setup_logger():
    # Resolve LOGS_DIR safely — works both in dev and as installed .exe
    try:
        from app.config.settings import LOGS_DIR
        log_dir = LOGS_DIR
    except Exception:
        log_dir = None

    # Fallback: use C:\StockManager\logs or temp folder
    if not log_dir:
        log_dir = r"C:\StockManager\logs"

    os.makedirs(log_dir, exist_ok=True)

    logger.remove()

    # Console output — skip when running as compiled exe (no console)
    if not getattr(sys, 'frozen', False):
        logger.add(
            sys.stdout,
            level="DEBUG",
            colorize=True,
            format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
        )

    # File output (rotating daily, keep 7 days)
    log_file = os.path.join(log_dir, "stock_manager_{time:YYYY-MM-DD}.log")
    logger.add(
        log_file,
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{line} | {message}"
    )




