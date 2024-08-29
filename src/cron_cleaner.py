import os
import time
from pathlib import Path
import schedule
from threading import Thread
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH

DAYS = 1

def startCronCleaner():
    flask_thread = Thread(target=run_scheduler)
    flask_thread.start()


def all_files_old(directory, cutoff):
    """Überprüft, ob alle Dateien in einem Verzeichnis älter sind als der cutoff-Zeitpunkt."""
    all_old = True
    for filename in os.listdir(directory):
        file_path = Path(directory) / filename
        if file_path.is_file():
            if os.path.getmtime(file_path) >= cutoff:
                all_old = False
                break
    return all_old

def delete_empty_directories(directory, days):
    now = time.time()
    cutoff = now - (days * 86400)  # Tage in Sekunden umrechnen

    def recursive_delete(dir_path):
        """Rekursiv leere Verzeichnisse löschen, wenn alle Dateien älter sind."""
        for entry in os.listdir(dir_path):
            entry_path = Path(dir_path) / entry
            if entry_path.is_dir():
                # Zuerst in Unterverzeichnisse gehen
                recursive_delete(entry_path)
        
        # Lösche das Verzeichnis, wenn alle Dateien und Unterverzeichnisse die Bedingung erfüllen
        if all_files_old(dir_path, cutoff) and not os.listdir(dir_path):
            try:
                os.rmdir(dir_path)
                print(f"Deleting folder {dir_path}...")
            except OSError as e:
                # Falls das Verzeichnis nicht gelöscht werden kann (z.B. weil es noch nicht leer ist)
                print(f"Could not delete folder {dir_path}: {e}")

    # Suche alle obersten Verzeichnisse im angegebenen Verzeichnis
    for item in os.listdir(directory):
        item_path = Path(directory) / item
        if item_path.is_dir():
            recursive_delete(item_path)



def run_cleanup():
    delete_old_files(DIRECTORY, DAYS)

def run_scheduler():
    schedule.every().day.at("00:00").do(run_cleanup)

    while True:
        schedule.run_pending()
        time.sleep(3600)  # wait to not use cpu.