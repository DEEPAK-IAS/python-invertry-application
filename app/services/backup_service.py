from __future__ import annotations
import shutil
import os
import json
import signal
import sys
import atexit
import traceback
from datetime import datetime, timedelta
from PySide2.QtCore import QThread, Signal, QTimer
from app.config.settings import BACKUP_DIR, DATABASE_URL
from app.utils.logger import logger
from app.config.settings import DB_FILE_PATH

DB_PATH = DB_FILE_PATH
BACKUP_META     = os.path.join(BACKUP_DIR, "backup_meta.json")
MAX_BACKUPS     = 10       # keep last 10 backups
AUTO_INTERVAL   = 30       # auto-backup every 30 minutes

def _do_backup(reason: str = "manual") -> str | None:
    """Create a backup and return path. Returns None on failure."""
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)

        if not os.path.exists(DB_PATH):
            logger.warning("Backup skipped — DB file not found")
            return None

        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{reason}_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_name)

        shutil.copy2(DB_PATH, backup_path)
        logger.info(f"Backup created [{reason}]: {backup_name}")

        _update_meta(backup_path, reason)
        _cleanup_old_backups()

        return backup_path

    except Exception as e:
        logger.error(f"Backup FAILED [{reason}]: {e}")
        return None


def _update_meta(backup_path: str, reason: str):
    """Track backup history in JSON."""
    meta = _load_meta()
    meta["backups"].append({
        "path":      backup_path,
        "reason":    reason,
        "timestamp": datetime.now().isoformat(),
        "size_kb":   round(os.path.getsize(backup_path) / 1024, 2),
    })
    meta["last_backup"] = datetime.now().isoformat()
    with open(BACKUP_META, "w") as f:
        json.dump(meta, f, indent=2)


def _load_meta() -> dict:
    if os.path.exists(BACKUP_META):
        try:
            with open(BACKUP_META, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"backups": [], "last_backup": None}


def _cleanup_old_backups():
    """Keep only the last MAX_BACKUPS files."""
    meta = _load_meta()
    backups = meta.get("backups", [])
    if len(backups) > MAX_BACKUPS:
        to_remove = backups[:-MAX_BACKUPS]
        for entry in to_remove:
            try:
                if os.path.exists(entry["path"]):
                    os.remove(entry["path"])
                    logger.info(f"Old backup removed: {entry['path']}")
            except Exception:
                pass
        meta["backups"] = backups[-MAX_BACKUPS:]
        with open(BACKUP_META, "w") as f:
            json.dump(meta, f, indent=2)


# ─────────────────────────────────────────
# 1. CRASH HANDLER — triggers on any unhandled exception
# ─────────────────────────────────────────
def _crash_handler(exc_type, exc_value, exc_tb):
    """Called automatically when Python crashes."""
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical(f"APP CRASHED:\n{error_msg}")
    logger.critical("Triggering emergency crash backup...")
    path = _do_backup(reason="crash")
    if path:
        logger.critical(f"Crash backup saved: {path}")
    else:
        logger.critical("Crash backup FAILED!")
    # Call original handler
    sys.__excepthook__(exc_type, exc_value, exc_tb)


# ─────────────────────────────────────────
# 2. EXIT HANDLER — triggers on normal app close
# ─────────────────────────────────────────
def _exit_handler():
    """Called when app closes normally."""
    logger.info("App closing — creating exit backup...")
    _do_backup(reason="exit")


# ─────────────────────────────────────────
# 3. AUTO BACKUP THREAD — runs every 30 minutes
# ─────────────────────────────────────────
class AutoBackupThread(QThread):
    backup_done   = Signal(str)   # emits backup path
    backup_failed = Signal()

    def __init__(self, interval_minutes: int = AUTO_INTERVAL):
        super().__init__()
        self.interval_ms = interval_minutes * 60 * 1000
        self._running    = True

    def run(self):
        waited = 0
        
        while self._running:
            # If we haven't reached the interval yet, sleep for 1 second and check again
            if waited < self.interval_ms:
                self.msleep(1000) # Sleep exactly 1 second
                waited += 1000
                continue
            
            # If we reach this point, the full interval has passed!
            path = _do_backup(reason="auto")
            if path:
                self.backup_done.emit(path)
            else:
                self.backup_failed.emit()
                
            # Reset the counter for the next cycle
            waited = 0

    def stop(self):
        self._running = False
        self.quit()


# ─────────────────────────────────────────
# 4. BackupService — main interface
# ─────────────────────────────────────────
class BackupService:
    _thread: AutoBackupThread = None

    @classmethod
    def setup(cls):
        """
        Call once at app startup.
        Registers crash handler, exit handler, and starts auto-backup thread.
        """
        # Register crash handler
        sys.excepthook = _crash_handler
        logger.info("Crash backup handler registered")

        # Register exit handler
        atexit.register(_exit_handler)
        logger.info("Exit backup handler registered")

        # Startup backup
        _do_backup(reason="startup")

        # Start auto-backup thread
        cls._thread = AutoBackupThread(interval_minutes=AUTO_INTERVAL)
        cls._thread.backup_done.connect(
            lambda path: logger.info(f"Auto-backup done: {path}")
        )
        cls._thread.backup_failed.connect(
            lambda: logger.warning("Auto-backup failed!")
        )
        cls._thread.start()
        logger.info(f"Auto-backup thread started (every {AUTO_INTERVAL} min)")

    @classmethod
    def manual_backup(cls) -> str | None:
        """Trigger a manual backup from UI."""
        return _do_backup(reason="manual")

    @classmethod
    def stop(cls):
        """Stop the auto-backup thread cleanly."""
        if cls._thread and cls._thread.isRunning():
            cls._thread.stop()
            cls._thread.wait()
            logger.info("Auto-backup thread stopped")

    @classmethod
    def get_history(cls) -> list:
        """Return list of all backups from meta file."""
        return _load_meta().get("backups", [])

    @classmethod
    def get_last_backup_time(cls) -> str | None:
        return _load_meta().get("last_backup")

    @classmethod
    def restore(cls, backup_path: str) -> bool:
        """Restore DB from a backup file."""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Restore failed — file not found: {backup_path}")
                return False
            # Backup current before restoring
            _do_backup(reason="pre_restore")
            shutil.copy2(backup_path, DB_PATH)
            logger.info(f"Database restored from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False



