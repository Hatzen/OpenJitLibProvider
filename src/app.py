import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, send_from_directory, render_template_string, abort, Response, url_for
from nexus_service import handleRepositoryCall
from ui_service import handle_list_files, handle_list_logs, handle_download_file, handle_clear_cache, handle_clear_all
from config import load_properties
import shutil
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH, LOCAL_LOGS_PATH

app = Flask(__name__)

@app.route("/repository/<path:artifact_path>", methods=["GET"])
def repository(artifact_path: str):
    handleRepositoryCall(artifact_path)

@app.route('/list')
def list_files():
     return handle_list_files()

@app.route('/logs')
def list_logs():
     return handle_list_logs()

@app.route('/download/<path:filename>')
def download_file(filename):
    return handle_download_file(LOCAL_REPO_PATH, filename)

@app.route('/log/<path:filename>')
def download_log(filename):
    return handle_download_file(LOCAL_LOGS_PATH, filename)

@app.route('/clear/cache')
def clear_cache():
    return handle_clear_cache()
    
@app.route('/clear/all')
def clear_all():
    return handle_clear_all()