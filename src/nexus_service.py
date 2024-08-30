import os
import sys

from flask import send_file, abort
from git_utils import clone_and_checkout, get_repo_url
from build_utils import update_build_files, build_project, find_artifact_file, save_artifact, getArtifactDest, getPackagings
from maven_utils import generate_maven_metadata, generate_pom_file
from error_handler import log_method_output
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH, LOCAL_CONFIG_FILE
from config import load_properties

config = load_properties(LOCAL_CONFIG_FILE)

def handleRepositoryCall(artifact_path: str):
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

    response = log_method_output(getArtifact, (organization, module, version, artifact_file), {}, organization, module, version, file_name)
    if response:
        return response
    abort(500, "Could not get or create artifact")
    

def getArtifact(organization, module, version, artifact_file):
    if not os.path.exists(artifact_file):
        artifact_file = handle_artifact_request(organization, module, version)

    print(artifact_file)
    if artifact_file and os.path.exists(artifact_file):
        # TODO: Why we need to get a folder up, when git and build is working fine and path exists..
        return send_file("../" + artifact_file)

    abort(404, "Artifact not found")

def handle_artifact_request(organization, module, version):
    repo_url = get_repo_url(organization, module)
    clone_dir = os.path.join(LOCAL_CLONE_PATH, f"{module}-{version}")
    os.makedirs(clone_dir, exist_ok=True)
    
    try:
        clone_and_checkout(repo_url, version, clone_dir)
        
        # TODO: build snapshots so build again
        if os.path.exists(os.path.join(clone_dir, "build")):
            # print(f"Build already exists, skipping: {clone_dir}")
            # TODO: Check if pom works..
            return os.path.join(getArtifactDest(organization, module, version))
        
        update_build_files(clone_dir)
        build_project(clone_dir)
        
        artifact_files = find_artifact_file(clone_dir)
        
        if artifact_files:
            dest_file = save_artifact(artifact_files, organization, module, version)
            packagings = getPackagings(artifact_files)
            generate_maven_metadata(organization, module, version, packagings)
            generate_pom_file(organization, module, version, packagings)
            return dest_file
        
        print(f"No build artifacts found: {clone_dir}")
        return None
    
    finally:
        pass  # Optional: Clean up by removing the cloned directory