import os
import sys
import shutil
import stat
from datetime import datetime
from flask import (
    send_file,
    render_template_string,
    abort,
    Response,
    jsonify,
    url_for,
    request
)
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH, LOCAL_LOGS_PATH
from config import get_config, reload_config
from cron_cleaner import run_cleanup_now

# CSS styling for modern dashboard
UI_STYLE = """
<style>
    :root {
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-card: #334155;
        --text-primary: #f8fafc;
        --text-muted: #94a3b8;
        --accent: #38bdf8;
        --accent-hover: #0ea5e9;
        --success: #22c55e;
        --danger: #ef4444;
        --border: #475569;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: var(--bg-primary);
        color: var(--text-primary);
        padding: 30px;
        line-height: 1.6;
    }
    .container { max-width: 1200px; margin: 0 auto; }
    header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
        border-bottom: 1px solid var(--border);
        padding-bottom: 20px;
    }
    h1 { font-size: 26px; color: var(--accent); }
    .badge {
        background: var(--bg-card);
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 13px;
        color: var(--text-muted);
    }
    nav { margin-bottom: 24px; display: flex; gap: 12px; }
    .nav-btn {
        background: var(--bg-secondary);
        color: var(--text-primary);
        text-decoration: none;
        padding: 10px 18px;
        border-radius: 8px;
        border: 1px solid var(--border);
        transition: all 0.2s;
    }
    .nav-btn:hover, .nav-btn.active {
        background: var(--accent);
        color: var(--bg-primary);
        font-weight: 600;
        border-color: var(--accent);
    }
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }
    .stat-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
    }
    .stat-title { font-size: 14px; color: var(--text-muted); margin-bottom: 8px; }
    .stat-value { font-size: 24px; font-weight: 700; color: var(--accent); }
    .card {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 30px;
    }
    .card h2 { font-size: 18px; margin-bottom: 16px; color: var(--text-primary); border-bottom: 1px solid var(--border); padding-bottom: 8px; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th, td { text-align: left; padding: 12px; border-bottom: 1px solid var(--border); font-size: 14px; }
    th { color: var(--text-muted); font-weight: 600; }
    tr:hover td { background: var(--bg-card); }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .btn {
        display: inline-block;
        padding: 8px 14px;
        border-radius: 6px;
        border: none;
        cursor: pointer;
        font-size: 13px;
        text-decoration: none;
        transition: 0.2s;
    }
    .btn-danger { background: var(--danger); color: white; }
    .btn-danger:hover { opacity: 0.9; }
    .btn-secondary { background: var(--bg-card); color: var(--text-primary); }
    .btn-secondary:hover { background: var(--border); }
    pre {
        background: #000;
        color: #38bdf8;
        padding: 18px;
        border-radius: 8px;
        overflow-x: auto;
        font-size: 13px;
        max-height: 600px;
    }
</style>
"""

def get_dir_size_and_count(path: str):
    total_size = 0
    file_count = 0
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total_size += os.path.getsize(fp)
                    file_count += 1
                except OSError:
                    pass
    return total_size, file_count

def format_bytes(bytes_num: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} TB"

def handle_dashboard():
    config = get_config()
    repo_size, repo_files = get_dir_size_and_count(LOCAL_REPO_PATH)
    tmp_size, tmp_files = get_dir_size_and_count(LOCAL_CLONE_PATH)
    logs_size, logs_files = get_dir_size_and_count(LOCAL_LOGS_PATH)

    hosts_html = "".join(f"<tr><td><code>{k}</code></td><td><code>{v}</code></td></tr>" for k, v in config.get("KNOWN_HOSTS", {}).items())

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>OpenJitLibProvider - Dashboard</title>
    {UI_STYLE}
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 OpenJitLibProvider</h1>
            <div class="badge">Port: {config.get('NEXUS_PORT')} | Ready to replace JitPack</div>
        </header>

        <nav>
            <a href="/" class="nav-btn active">Dashboard</a>
            <a href="/list" class="nav-btn">Artifacts Browser</a>
            <a href="/logs" class="nav-btn">Build Logs</a>
            <a href="/repository/" class="nav-btn">Maven Index</a>
        </nav>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">Cached Artifacts</div>
                <div class="stat-value">{repo_files}</div>
                <div class="stat-title" style="margin-top:4px;">Size: {format_bytes(repo_size)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Build Logs</div>
                <div class="stat-value">{logs_files}</div>
                <div class="stat-title" style="margin-top:4px;">Size: {format_bytes(logs_size)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Temp Build Storage</div>
                <div class="stat-value">{format_bytes(tmp_size)}</div>
                <div class="stat-title" style="margin-top:4px;">{tmp_files} temp files</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Status</div>
                <div class="stat-value" style="color:var(--success);">Active</div>
                <div class="stat-title" style="margin-top:4px;">Auto-Cleanup: {'On' if config.get('DELETE_TMP', -1) > 0 else 'Off'}</div>
            </div>
        </div>

        <div class="card">
            <h2>Quick Actions</h2>
            <div style="display:flex; gap:12px; flex-wrap:wrap;">
                <a href="/api/reload_config" class="btn btn-secondary">🔄 Reload Config</a>
                <a href="/cleanup/run" class="btn btn-secondary">🧹 Run Scheduled Cleanup Now</a>
                <a href="/clear/cache" onclick="return confirm('Clear build cache?');" class="btn btn-danger">🗑️ Clear Build Cache</a>
                <a href="/clear/logs" onclick="return confirm('Clear build logs?');" class="btn btn-danger">🗑️ Clear Build Logs</a>
                <a href="/clear/all" onclick="return confirm('Clear everything including repo artifacts?');" class="btn btn-danger">⚠️ Clear All Storage</a>
            </div>
        </div>

        <div class="card">
            <h2>Supported Git Hosts</h2>
            <table>
                <thead><tr><th>Package Prefix</th><th>Git Host URL</th></tr></thead>
                <tbody>{hosts_html}</tbody>
            </table>
        </div>
    </div>
</body>
</html>"""
    return Response(html, mimetype="text/html")

def handle_list_files():
    return handle_list(LOCAL_REPO_PATH, "Artifacts Repository", "download_file")

def handle_list_logs():
    return handle_list(LOCAL_LOGS_PATH, "Build Logs", "download_log")

def handle_list(base_dir: str, title: str, download_endpoint: str):
    items = []
    if os.path.exists(base_dir):
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir).replace(os.sep, '/')
                size = os.path.getsize(full_path)
                mtime = os.path.getmtime(full_path)
                date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                items.append({
                    "path": rel_path,
                    "filename": file,
                    "size": format_bytes(size),
                    "date": date_str
                })

    items.sort(key=lambda x: x["path"])
    rows = ""
    for it in items:
        link = url_for(download_endpoint, filename=it["path"])
        rows += f'<tr><td><a href="{link}">{it["path"]}</a></td><td>{it["size"]}</td><td>{it["date"]}</td></tr>'

    if not rows:
        rows = '<tr><td colspan="3" style="text-align:center; color:var(--text-muted);">No files found in directory.</td></tr>'

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title} - OpenJitLibProvider</title>
    {UI_STYLE}
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <a href="/" class="btn btn-secondary">← Back to Dashboard</a>
        </header>

        <nav>
            <a href="/" class="nav-btn">Dashboard</a>
            <a href="/list" class="nav-btn {'active' if 'Artifact' in title else ''}">Artifacts</a>
            <a href="/logs" class="nav-btn {'active' if 'Log' in title else ''}">Build Logs</a>
        </nav>

        <div class="card">
            <table>
                <thead><tr><th>File Path</th><th>Size</th><th>Last Modified</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>
</body>
</html>"""
    return Response(html, mimetype="text/html")

def handle_download_file(folder: str, filename: str):
    target = os.path.abspath(os.path.join(folder, filename))
    if not os.path.exists(target):
        abort(404, f"File {filename} not found.")

    # If it's a log file requested in browser, display nicely formatted
    if target.endswith(".txt") and request.args.get("raw") != "1":
        try:
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Log: {filename}</title>
    {UI_STYLE}
</head>
<body>
    <div class="container">
        <header>
            <h1>📄 Log: {filename}</h1>
            <div>
                <a href="?raw=1" class="btn btn-secondary">Raw View</a>
                <a href="/logs" class="btn btn-secondary">← Back to Logs</a>
            </div>
        </header>
        <pre>{content}</pre>
    </div>
</body>
</html>"""
            return Response(html, mimetype="text/html")
        except Exception:
            pass

    return send_file(target)

def handle_clear_cache():
    if os.path.exists(LOCAL_CLONE_PATH):
        try:
            rmtree(LOCAL_CLONE_PATH)
            os.makedirs(LOCAL_CLONE_PATH, exist_ok=True)
        except Exception as e:
            abort(400, description=f"Failed to clear cache: {e}")
    return jsonify({"status": "success", "message": "Cache cleared successfully"})

def handle_clear_logs():
    if os.path.exists(LOCAL_LOGS_PATH):
        try:
            rmtree(LOCAL_LOGS_PATH)
            os.makedirs(LOCAL_LOGS_PATH, exist_ok=True)
        except Exception as e:
            abort(400, description=f"Failed to clear logs: {e}")
    return jsonify({"status": "success", "message": "Logs cleared successfully"})

def handle_clear_all():
    handle_clear_cache()
    handle_clear_logs()
    if os.path.exists(LOCAL_REPO_PATH):
        try:
            rmtree(LOCAL_REPO_PATH)
            os.makedirs(LOCAL_REPO_PATH, exist_ok=True)
        except Exception as e:
            abort(400, description=f"Failed to clear repository artifacts: {e}")
    return jsonify({"status": "success", "message": "All storage (cache, logs, repository) cleared"})

def handle_stats():
    repo_size, repo_files = get_dir_size_and_count(LOCAL_REPO_PATH)
    tmp_size, tmp_files = get_dir_size_and_count(LOCAL_CLONE_PATH)
    logs_size, logs_files = get_dir_size_and_count(LOCAL_LOGS_PATH)
    config = get_config()

    return jsonify({
        "status": "healthy",
        "artifacts_count": repo_files,
        "artifacts_size_bytes": repo_size,
        "logs_count": logs_files,
        "logs_size_bytes": logs_size,
        "tmp_size_bytes": tmp_size,
        "config": {
            "port": config.get("NEXUS_PORT"),
            "delete_artifacts_days": config.get("DELETE_ARTIFACTS"),
            "delete_tmp_days": config.get("DELETE_TMP"),
            "known_hosts": config.get("KNOWN_HOSTS", {})
        }
    })

def handle_reload_config():
    new_cfg = reload_config()
    return jsonify({"status": "success", "message": "Configuration reloaded successfully", "config": new_cfg})

def handle_run_cleanup():
    run_cleanup_now()
    return jsonify({"status": "success", "message": "Scheduled cleanup executed successfully"})

def rmtree(top):
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            try:
                os.chmod(filename, stat.S_IWUSR | stat.S_IRUSR)
                os.remove(filename)
            except OSError:
                pass
        for name in dirs:
            try:
                os.rmdir(os.path.join(root, name))
            except OSError:
                pass
    try:
        os.rmdir(top)
    except OSError:
        pass