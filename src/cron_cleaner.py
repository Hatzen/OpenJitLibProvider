import os
import time
import shutil
from pathlib import Path
from threading import Thread
import schedule
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH
from config import get_config

def startCronCleaner():
    """Starts the background cleaner daemon thread."""
    cleaner_thread = Thread(target=run_scheduler, daemon=True)
    cleaner_thread.start()

def is_folder_older_than(dir_path: str, cutoff_timestamp: float) -> bool:
    """Checks if a directory and all files inside it are older than cutoff_timestamp."""
    try:
        if os.path.getmtime(dir_path) >= cutoff_timestamp:
            return False
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                f_path = os.path.join(root, file)
                if os.path.getmtime(f_path) >= cutoff_timestamp:
                    return False
        return True
    except (FileNotFoundError, OSError):
        return False

def clean_tmp_directories(max_days: int):
    """Deletes temporary build folders in LOCAL_CLONE_PATH older than max_days."""
    if max_days <= 0 or not os.path.exists(LOCAL_CLONE_PATH):
        return

    cutoff = time.time() - (max_days * 86400)
    for entry in os.listdir(LOCAL_CLONE_PATH):
        entry_path = os.path.join(LOCAL_CLONE_PATH, entry)
        if os.path.isdir(entry_path):
            if is_folder_older_than(entry_path, cutoff):
                print(f"[CronCleaner] Deleting old build clone: {entry_path}")
                try:
                    shutil.rmtree(entry_path, ignore_errors=True)
                except Exception as e:
                    print(f"[CronCleaner] Error removing {entry_path}: {e}")

def clean_old_artifacts(max_days: int):
    """Deletes cached repository artifacts in LOCAL_REPO_PATH older than max_days."""
    if max_days <= 0 or not os.path.exists(LOCAL_REPO_PATH):
        return

    cutoff = time.time() - (max_days * 86400)
    for root, dirs, files in os.walk(LOCAL_REPO_PATH, topdown=False):
        for file in files:
            f_path = os.path.join(root, file)
            try:
                # Use max of atime and mtime
                stat = os.stat(f_path)
                last_used = max(stat.st_mtime, getattr(stat, 'st_atime', stat.st_mtime))
                if last_used < cutoff:
                    print(f"[CronCleaner] Deleting expired artifact: {f_path}")
                    os.remove(f_path)
            except Exception as e:
                print(f"[CronCleaner] Error checking/removing artifact {f_path}: {e}")

    # Remove empty directories
    delete_empty_directories(LOCAL_REPO_PATH)

def delete_empty_directories(directory: str):
    """Recursively removes empty directories."""
    if not os.path.exists(directory):
        return
    for root, dirs, files in os.walk(directory, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except OSError:
                pass

def run_cleanup_now():
    """Runs a complete cleanup pass immediately."""
    config = get_config()
    delete_tmp_days = int(config.get("DELETE_TMP", -1))
    delete_artifacts_days = int(config.get("DELETE_ARTIFACTS", -1))

    print(f"[CronCleaner] Starting cleanup (DELETE_TMP={delete_tmp_days}, DELETE_ARTIFACTS={delete_artifacts_days})")
    if delete_tmp_days > 0:
        clean_tmp_directories(delete_tmp_days)
    if delete_artifacts_days > 0:
        clean_old_artifacts(delete_artifacts_days)

def run_scheduler():
    # Schedule daily cleanup at midnight
    schedule.every().day.at("00:00").do(run_cleanup_now)
    # Also run every hour to check pending
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"[CronCleaner] Scheduler error: {e}")
        time.sleep(300)