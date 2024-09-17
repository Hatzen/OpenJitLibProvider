import os
import subprocess
import shutil
from flask import Flask, jsonify, send_file

app = Flask(__name__)

BUILD_DIR = "/tmp/cpp-conan"
PACKAGE_DIR = "/tmp/cpp-packages"
GITHUB_ORG = "my-org"  # Example: your GitHub organization or username

def clone_repo(package_name, version, build_dir):
    """
    Clone the GitHub repository for the given C++ package and version (branch/tag).
    """
    repo_url = f"https://github.com/{GITHUB_ORG}/{package_name}.git"
    
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    subprocess.run(["git", "clone", "--branch", version, repo_url, build_dir])

def create_conan_package(build_dir):
    """
    Build the Conan package.
    Assumes the project has a `conanfile.py` or `conanfile.txt`.
    """
    if not os.path.exists(os.path.join(build_dir, "conanfile.py")) and not os.path.exists(os.path.join(build_dir, "conanfile.txt")):
        raise FileNotFoundError("No conanfile found in project")

    subprocess.run(["conan", "create", build_dir, "."], cwd=build_dir)

@app.route("/<package_name>/-/<package_name>-<version>.tar.gz", methods=["GET"])
def serve_package(package_name, version):
    """
    Endpoint to serve the C++ Conan package.
    """
    build_dir = os.path.join(BUILD_DIR, package_name, version)
    
    try:
        # 1. Clone the repository from GitHub
        clone_repo(package_name, version, build_dir)
        
        # 2. Build the Conan package
        create_conan_package(build_dir)

        # 3. Serve the package (e.g., serve the conan recipe or binary)
        conan_package_path = os.path.join(build_dir, "conan_package")  # Adjust this as necessary
        return send_file(conan_package_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def build_package(build_dir):
    """
    Use setuptools or poetry to build the Python package.
    This function assumes either 'setup.py' or 'pyproject.toml' is present.
    """
    if os.path.exists(os.path.join(build_dir, "setup.py")):
        # Build using setuptools (creates a wheel and sdist)
        subprocess.run(["python3", "-m", "build"], cwd=build_dir)
    elif os.path.exists(os.path.join(build_dir, "pyproject.toml")):
        # Build using poetry (creates a wheel and sdist)
        subprocess.run(["poetry", "build"], cwd=build_dir)
    else:
        raise FileNotFoundError("No setup.py or pyproject.toml found in project")

def create_package(build_dir, package_name, version):
    """
    Package the built Python project as a wheel or sdist for distribution.
    """
    dist_dir = os.path.join(build_dir, "dist")
    if not os.path.exists(dist_dir):
        raise FileNotFoundError(f"No 'dist' directory found in {build_dir}")

    # Return the wheel or sdist file path
    dist_files = os.listdir(dist_dir)
    if not dist_files:
        raise FileNotFoundError(f"No distribution files found in {dist_dir}")

    return os.path.join(dist_dir, dist_files[0])

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