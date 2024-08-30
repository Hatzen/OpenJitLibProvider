import os
import sys
import shutil
import stat

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, send_file, send_from_directory, render_template_string, abort, Response, url_for
from nexus_service import handleRepositoryCall
from config import load_properties
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH, LOCAL_LOGS_PATH


def handle_list_files():
    return handle_list(LOCAL_REPO_PATH, "download_file")
    
def handle_list_logs():
    return handle_list(LOCAL_LOGS_PATH, "download_log") # Name of the method in app.py

def handle_download_file(folder, filename):
    print(f"getting {folder} & {filename}")
    return send_file("../" + filename)
    # TODO: Remove
    # return send_file("../" + filename, as_attachment=True)
    # return send_file(filename, as_attachment=True)
    # return send_from_directory("..", filename, as_attachment=True)

# shutil.rmtree leads to fail
def handle_clear_cache():
    if os.path.exists(LOCAL_CLONE_PATH):
        try:
            rmtree(LOCAL_CLONE_PATH)
        except Exception as e:
            abort("Failed to delete folder, probably build ongoing.", e, 400)
            return
    return Response(status=200, mimetype='text/plain')


def handle_clear_all():
    handle_clear_cache()
    if os.path.exists(LOCAL_LOGS_PATH):
        try:
            rmtree(LOCAL_LOGS_PATH)
        except Exception as e:
            abort("Failed to delete folder, probably build ongoing.", e, 400)
            return
    if os.path.exists(LOCAL_LOGS_PATH):
        try:
            rmtree(LOCAL_LOGS_PATH)
        except Exception as e:
            abort("Failed to delete folder, probably build ongoing.", e, 400)
            return
    return Response(status=200, mimetype='text/plain')

def handle_list(dir, download_method_name):
     # Get a list of files and directories
    items = list_files_recursively(dir)

    # Prepare the HTML response
    def generate_html(items):
        html = []
        def add_item(path, is_file):
            depth = path.count(os.sep) - dir.count(os.sep) + 1
            indentation = 'style="margin-left: {}px;"'.format(depth * 20)
            if is_file:
                html.append(f'<li><a href="{url_for(download_method_name, filename=path)}">{os.path.basename(path)}</a></li>')
            else:
                html.append(f'<li {indentation}>{os.path.basename(path)}<ul>')
                for item in items:
                    item_path, item_is_file = item
                    if item_path.startswith(path + os.sep) and item_path.count(os.sep) == path.count(os.sep) + 1:
                        add_item(item_path, item_is_file)
                html.append('</ul></li>')

        for item in items:
            path, is_file = item
            if path.count(os.sep) == 0:  # Only start from the root directory
                add_item(path, is_file)

        return ''.join(html)

    html_content = generate_html(items)
    return render_template_string(f'''
    <h1>Files in Directory</h1>
    <ul>
        {html_content}
    </ul>
    ''')

def list_files_recursively(directory, depth=0):
    items = []
    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                items.append((item_path, False))
                items.extend(list_files_recursively(item_path, depth + 1))
            else:
                items.append((item_path, True))
    except PermissionError:
        # Handle the case where access to a directory is denied
        pass
    return items

# https://stackoverflow.com/a/2656408/8524651
def rmtree(top):
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(top)  