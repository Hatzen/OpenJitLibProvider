import os
import subprocess
from flask import Flask, request, send_file, abort

# Konfiguration
GITHUB_ORG = "example-org"
LOCAL_REPO_PATH = "/path/to/local/repo"

app = Flask(__name__)

def get_github_repo_url(organization, module):
    return f"https://github.com/{organization}/{module}.git"

def clone_and_checkout(repo_url, version, clone_dir):
    subprocess.run(["git", "clone", repo_url, clone_dir], check=True)
    subprocess.run(["git", "-C", clone_dir, "checkout", version], check=True)

def build_project(clone_dir):
    subprocess.run(["./gradlew", "clean", "build"], cwd=clone_dir, check=True)

def handle_artifact_request(organization, module, version):
    repo_url = get_github_repo_url(organization, module)
    clone_dir = os.path.join("/tmp", f"{module}-{version}")
    
    if not os.path.exists(clone_dir):
        os.makedirs(clone_dir)
        
    try:
        clone_and_checkout(repo_url, version, clone_dir)
        build_project(clone_dir)
        
        jar_file = os.path.join(clone_dir, "build", "libs", f"{module}-{version}.jar")
        if os.path.exists(jar_file):
            group_path = organization.replace('.', '/')
            dest_dir = os.path.join(LOCAL_REPO_PATH, group_path, module, version)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
                
            dest_file = os.path.join(dest_dir, f"{module}-{version}.jar")
            os.rename(jar_file, dest_file)
            return dest_file
        else:
            return None
    finally:
        subprocess.run(["rm", "-rf", clone_dir])

@app.route("/repository/<path:artifact_path>", methods=["GET"])
def repository(artifact_path):
    parts = artifact_path.split('/')
    if len(parts) < 4:
        abort(400, "Ungültige Artefakt-URL")

    organization = parts[0]
    module = parts[1]
    version = parts[2]
    file_name = parts[-1]
    
    artifact_dir = os.path.join(LOCAL_REPO_PATH, organization, module, version)
    artifact_file = os.path.join(artifact_dir, file_name)
    
    if not os.path.exists(artifact_file):
        artifact_file = handle_artifact_request(organization, module, version)
    
    if artifact_file and os.path.exists(artifact_file):
        return send_file(artifact_file)
    else:
        abort(404, "Artefakt nicht gefunden")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)