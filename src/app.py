import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, request, send_file, abort
from git_utils import clone_and_checkout
from build_utils import update_build_files, build_project, find_artifact_file, save_artifact
from maven_utils import generate_maven_metadata, generate_pom_file
from error_handler import log_method_output

# Load configuration
LOCAL_REPO_PATH = "../repo/"
LOCAL_CLONE_PATH = "../tmp/"

app = Flask(__name__)

@app.route("/repository/<path:artifact_path>", methods=["GET"])
def repository(artifact_path: str):
    if "com/github/" not in artifact_path: 
        abort(404, "No GitHub URL found")

    artifact_path = artifact_path.replace("com/github/", "")
    parts = artifact_path.split('/')

    if len(parts) < 4 or len(parts) > 4:
        abort(404 if len(parts) > 4 else 400, "Invalid artifact URL")

    organization, module, version, file_name = parts[0], parts[1], parts[2], parts[-1]
    # version = parts[2].replace("-SNAPSHOT", "") # Remove Snapshot for some repos, but it might be needed..
    artifact_dir = os.path.join(LOCAL_REPO_PATH, organization, module, version)
    artifact_file = os.path.join(artifact_dir, file_name)

    if not os.path.exists(artifact_file):
        artifact_file = handle_artifact_request(organization, module, version)

    if artifact_file and os.path.exists(artifact_file):
        return send_file(artifact_file)

    abort(404, "Artifact not found")
    # log_method_output(getArtifact, (organization, module, version, artifact_file), {}, organization, module, version, file_name)
    

    # def getArtifact(organization, module, version, artifact_file):
    #    if not os.path.exists(artifact_file):
    #        artifact_file = handle_artifact_request(organization, module, version)

    #    if artifact_file and os.path.exists(artifact_file):
    #        return send_file(artifact_file)

    #    abort(404, "Artifact not found")

def handle_artifact_request(organization, module, version):
    repo_url = f"https://github.com/{organization}/{module}.git"
    clone_dir = os.path.join(LOCAL_CLONE_PATH, f"{module}-{version}")
    os.makedirs(clone_dir, exist_ok=True)
    
    try:
        clone_and_checkout(repo_url, version, clone_dir)
        
        if os.path.exists(os.path.join(clone_dir, "build")):
            print(f"Build already exists, skipping: {clone_dir}")
            return None
        
        update_build_files(clone_dir)
        build_project(clone_dir)
        
        jar_file = find_artifact_file(clone_dir)
        
        if jar_file:
            dest_file = save_artifact(jar_file, organization, module, version)
            generate_maven_metadata(organization, module, version)
            generate_pom_file(organization, module, version)
            return dest_file
        
        print(f"AAR file not found: {clone_dir}")
        return None
    
    finally:
        pass  # Optional: Clean up by removing the cloned directory