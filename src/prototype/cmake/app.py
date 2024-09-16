import os
import subprocess
import tarfile
import shutil
from flask import Flask, jsonify, send_file, request

app = Flask(__name__)

# Directories for cloning, building, and packaging
BUILD_DIR = "/tmp/cpp-builds"
PACKAGE_DIR = "/tmp/cpp-packages"
GITHUB_ORG = "my-org"  # Example: your GitHub organization or username

def clone_repo(package_name, version, build_dir):
    """
    Clone the GitHub repository for the given C++ package and version (branch/tag).
    """
    repo_url = f"https://github.com/{GITHUB_ORG}/{package_name}.git"
    
    # Clean up previous build directory
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    # Clone the repository and check out the specified version
    subprocess.run(["git", "clone", "--branch", version, repo_url, build_dir])

def build_project(build_dir):
    """
    Use CMake to build the C++ project.
    Assumes CMakeLists.txt is present in the project root.
    """
    build_subdir = os.path.join(build_dir, "build")
    os.makedirs(build_subdir, exist_ok=True)
    
    # Run CMake to configure and build the project
    subprocess.run(["cmake", ".."], cwd=build_subdir)
    subprocess.run(["cmake", "--build", "."], cwd=build_subdir)

def create_package(build_dir, package_name, version):
    """
    Package the built project as a tarball (or zip) for distribution.
    """
    package_path = os.path.join(PACKAGE_DIR, f"{package_name}-{version}.tar.gz")
    
    # Remove any previous package
    if os.path.exists(package_path):
        os.remove(package_path)

    # Create a new tarball from the build directory
    with tarfile.open(package_path, "w:gz") as tar:
        tar.add(build_dir, arcname=os.path.basename(build_dir))
    
    return package_path

@app.route("/<package_name>/-/<package_name>-<version>.tar.gz", methods=["GET"])
def serve_package(package_name, version):
    """
    Endpoint to serve the C++ package as a tarball based on package name and version.
    """
    build_dir = os.path.join(BUILD_DIR, package_name, version)
    
    try:
        # 1. Clone the repository from GitHub
        clone_repo(package_name, version, build_dir)
        
        # 2. Build the project using CMake
        build_project(build_dir)
        
        # 3. Package the built project
        package_path = create_package(build_dir, package_name, version)
        
        # 4. Serve the package as a file download
        return send_file(package_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/<package_name>", methods=["GET"])
def package_metadata(package_name):
    """
    Provides metadata to the client to recognize the package and its available versions.
    """
    # You could fetch actual version info from tags or a database
    version = "1.0.0"
    metadata = {
        "name": package_name,
        "dist-tags": {
            "latest": version
        },
        "versions": {
            version: {
                "dist": {
                    "tarball": f"http://localhost:5000/{package_name}/-/{package_name}-{version}.tar.gz"
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