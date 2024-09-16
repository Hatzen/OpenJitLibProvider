import os
import subprocess
import tarfile
import shutil
from flask import Flask, jsonify, send_file, request

app = Flask(__name__)

# Directory for cloning and building the projects
BUILD_DIR = "/tmp/npm-builds"
PACKAGE_DIR = "/tmp/npm-packages"
GITHUB_ORG = "my-org"  # Example: your GitHub organization or username

def clone_repo(package_name, version, build_dir):
    """
    Clone the GitHub repository based on the package name and version.
    The version will be used as the branch or tag.
    """
    repo_url = f"https://github.com/{GITHUB_ORG}/{package_name}.git"
    
    # Clean up any previous builds
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    # Clone the repository and check out the correct version (branch or tag)
    subprocess.run(["git", "clone", "--branch", version, repo_url, build_dir])

def build_project(build_dir):
    """
    Run npm install and npm pack to build the project.
    The project will be built into a tarball (.tgz) package.
    """
    subprocess.run(["npm", "install"], cwd=build_dir)
    subprocess.run(["npm", "pack"], cwd=build_dir)

def create_tarball(build_dir, package_name, version):
    """
    Create a tarball of the npm package and save it in the PACKAGE_DIR.
    This tarball will be served when npm requests the package.
    """
    tarball_path = os.path.join(PACKAGE_DIR, f"{package_name}-{version}.tgz")
    
    # Remove any previous tarballs for this package
    if os.path.exists(tarball_path):
        os.remove(tarball_path)

    # Create a new tarball
    with tarfile.open(tarball_path, "w:gz") as tar:
        tar.add(build_dir, arcname=os.path.basename(build_dir))
    
    return tarball_path

@app.route("/<package_name>/-/<package_name>-<version>.tgz", methods=["GET"])
def serve_package(package_name, version):
    """
    Endpoint to serve the package tarball (.tgz) based on package name and version.
    """
    build_dir = os.path.join(BUILD_DIR, package_name, version)
    
    try:
        # 1. Clone the repository
        clone_repo(package_name, version, build_dir)
        
        # 2. Build the project
        build_project(build_dir)
        
        # 3. Create a tarball of the package
        tarball_path = create_tarball(build_dir, package_name, version)
        
        # 4. Serve the tarball as a file download
        return send_file(tarball_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/<package_name>", methods=["GET"])
def package_metadata(package_name):
    """
    Endpoint to provide package metadata to npm.
    This allows npm to recognize the package and the available versions.
    """
    # You could also fetch available versions from a real tag system or database
    version = "1.0.0"
    metadata = {
        "name": package_name,
        "dist-tags": {
            "latest": version
        },
        "versions": {
            version: {
                "dist": {
                    "tarball": f"http://localhost:5000/{package_name}/-/{package_name}-{version}.tgz"
                }
            }
        }
    }
    return jsonify(metadata)

if __name__ == "__main__":
    # Ensure the package directory exists
    if not os.path.exists(PACKAGE_DIR):
        os.makedirs(PACKAGE_DIR)
    # Run the server
    app.run(debug=True, host="0.0.0.0", port=5000)