import os
import sys

from flask import send_file, abort
from git_utils import *
from build_utils.build_wrapper import build
from build_utils.build_utils import *
from maven_utils import generate_maven_metadata, generate_pom_file
from error_handler import log_method_output
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH, LOCAL_CONFIG_FILE
from config import load_properties

config = load_properties(LOCAL_CONFIG_FILE)

def handleRepositoryCall(artifact_path: str):
    targetHostUrl = ""
    parts = []
    for hostPackage, hostUrl in config["KNOWN_HOSTS"].items():
        hostPackageUrl = hostPackage.replace(".", "/")
        if hostPackageUrl not in artifact_path: 
            continue

        artifact_path = artifact_path.replace(hostPackageUrl+ "/", "")
        parts = artifact_path.split('/')
        targetHostUrl = hostUrl
        break
    
    # print(parts)
    print(artifact_path + " pulling from " + targetHostUrl)
    
    if not parts: 
        abort(404, "No matching host found. Maybe add one to KNOWN_HOSTS within config.")

    if len(parts) < 4 or len(parts) > 5:
        abort(400, "Invalid artifact URL")

    organization, repo, version, file_name = parts[0], parts[1], parts[2], parts[-1]
    if len(parts) == 5:
        module = parts[3]
    else:
        module = repo
    artifact_dir = os.path.join(LOCAL_REPO_PATH, organization, repo, version)

    # TODO: Needs fix for module
    artifact_file = os.path.join(artifact_dir, file_name)

    response = log_method_output(getArtifact, (targetHostUrl, organization, repo, version, artifact_file),
                    {}, organization, repo, module, version, file_name)
    if response:
        return response
    abort(500, "Could not get or create artifact")
    

def getArtifact(targetHostUrl, organization, repo, module, version, artifact_file):
    print("getArtifact: " + artifact_file)
    # TODO: do we need this to handle maven files like pom and metadata differently?
    # TODO: pass and use module somehow
    artifact_file = handle_artifact_request(targetHostUrl, organization, repo, version)

    if artifact_file and os.path.exists(artifact_file):
        # TODO: Why we need to get a folder up, when git and build is working fine and path exists..
        return send_file("../" + artifact_file)
    else:
        abort(404, "Artifact not found: " + str(artifact_file))

def handle_artifact_request(targetHostUrl, organization, repo, version):
    repo_url = get_repo_url(targetHostUrl, organization, repo)
    clone_dir = os.path.join(LOCAL_CLONE_PATH, f"{repo}-{version}")
    os.makedirs(clone_dir, exist_ok=True)
    
    try:
        print("clone and checkout")
        clone_and_checkout(repo_url, version, clone_dir)

        print("check hash")
        artifactFolder = getArtifactDest(organization, repo, version)
        needsToBeBuild = checkCommitHashAndUpdate(clone_dir, artifactFolder)

        generatedFileExists = os.path.exists(os.path.join(artifactFolder, "*.sha1"))
        if not needsToBeBuild and generatedFileExists:
             print(f"Artifact already exists, using {artifactFolder}")
             artifact_files = find_artifact_file(clone_dir)
             return os.path.join(artifact_files)
        
        print("Artifact needs fresh build")
        
        build(clone_dir)
        
        print("Find artifacts")
        artifact_files = find_artifact_file(clone_dir)
        print("list artifact files")
        print(artifact_files)
        
        if artifact_files:
            # TODO: when artifact already exists write log or fail, or keep original name somehow?
            dest_file = save_artifact(artifact_files, organization, repo, version)
            print("dest_file")
            print(dest_file)
            packaging = getPackagings(artifact_files)
            print("packaging")
            print(packaging)
            generate_maven_metadata(organization, repo, version)
            generate_pom_file(organization, repo, version, packaging)
            print("finished serving file " + dest_file)
            return dest_file
        
        print(f"No build artifacts found: {clone_dir}")
        return None
    
    finally:
        pass  # Optional: Clean up by removing the cloned directory