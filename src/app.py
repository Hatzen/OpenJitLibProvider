import os
import sys

# Ensure src directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from flask import Flask, jsonify, abort
from nexus_service import handleRepositoryCall
from ui_service import (
    handle_dashboard,
    handle_list_files,
    handle_list_logs,
    handle_download_file,
    handle_clear_cache,
    handle_clear_logs,
    handle_clear_all,
    handle_stats,
    handle_reload_config,
    handle_run_cleanup
)
from consts import LOCAL_REPO_PATH, LOCAL_LOGS_PATH

app = Flask(__name__)

@app.route("/")
def index():
    return handle_dashboard()

@app.route("/repository/", defaults={"artifact_path": ""}, methods=["GET"])
@app.route("/repository/<path:artifact_path>", methods=["GET"])
def repository(artifact_path: str):
    return handleRepositoryCall(artifact_path)

@app.route("/list")
def list_files():
    return handle_list_files()

@app.route("/logs")
def list_logs():
    return handle_list_logs()

@app.route("/download/<path:filename>")
def download_file(filename):
    return handle_download_file(LOCAL_REPO_PATH, filename)

@app.route("/log/<path:filename>")
def download_log(filename):
    return handle_download_file(LOCAL_LOGS_PATH, filename)

@app.route("/status")
@app.route("/api/stats")
def stats():
    return handle_stats()

@app.route("/api/reload_config", methods=["GET", "POST"])
def reload_configuration():
    return handle_reload_config()

@app.route("/cleanup/run", methods=["GET", "POST"])
def trigger_cleanup():
    return handle_run_cleanup()

@app.route("/clear/cache")
def clear_cache():
    return handle_clear_cache()

@app.route("/clear/logs")
def clear_logs():
    return handle_clear_logs()

@app.route("/clear/all")
def clear_all():
    return handle_clear_all()

@app.route("/refresh/<path:artifact_path>")
def refresh_artifact(artifact_path: str):
    """Force re-clone and rebuild of a specific artifact."""
    clean_path = artifact_path.strip("/")
    target = os.path.join(LOCAL_REPO_PATH, *clean_path.split("/"))
    if os.path.exists(target):
        try:
            if os.path.isdir(target):
                import shutil
                shutil.rmtree(target)
            else:
                os.remove(target)
        except Exception as e:
            abort(400, description=f"Could not remove cached artifact: {e}")
    return handleRepositoryCall(artifact_path)