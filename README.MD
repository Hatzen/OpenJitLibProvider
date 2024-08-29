# Custom Maven Artifact Repository with GitHub Integration

This project provides a custom Maven artifact repository using Flask, which clones, builds, and serves artifacts from GitHub repositories. It supports building Android libraries and generating necessary Maven metadata for the artifacts.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features
- Clones GitHub repositories for specified modules and versions.
- Builds Android libraries (AAR files).
- Generates Maven metadata (POM files and SHA-1 hashes).
- Serves built artifacts and metadata through a Flask-based web server.

## Prerequisites
- Python 3.x
- Git
- Java (JDK 8 or 11 recommended)
- Android SDK
- Flask

## Installation

### Clone the Repository:
```bash
git clone https://github.com/yourusername/custom-maven-repo.git
cd custom-maven-repo
```

### Install Python Dependencies:
```bash
pip install -r requirements.txt
```

### Set Up Java and Android SDK:
Ensure you have the correct paths for `JAVA_HOME` and `ANDROID_SDK_ROOT` in your system.

## Configuration

### Create the `properties.config` File:
In the project root directory, create a `properties.config` file with the following structure:

```ini
[ENVIRONMENT]
JAVA_HOME=C:/path/to/java/home
ANDROID_SDK_ROOT=C:/path/to/android/sdk
```
Replace the paths with your actual installation paths.

### Modify Configuration (Optional):
If needed, you can modify the `config.py` file to handle additional configuration settings.

## Usage

### Run the Flask Server:
```bash
python app.py
```

### Access the Repository:
You can now access the repository via `http://localhost:5000/repository/`.

### Requesting Artifacts:
To request an artifact, use a URL in the following format:

```bash
http://localhost:5000/repository/com/github/{organization}/{module}/{version}/{artifact-filename}
```

#### Example:
```bash
http://localhost:5000/repository/com/github/skydoves/ElasticViews/1.0.6/ElasticViews-1.0.6.aar
```

## Project Structure
```plaintext
custom-maven-repo/
│
├── app.py                     # Main Flask application
├── build_tools.py             # Functions for building projects
├── git_utils.py               # Git-related functions for cloning and checkout
├── maven_metadata.py          # Functions for generating Maven metadata
├── config.py                  # Configuration loader
├── properties.config          # Configuration file for environment variables
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

## Troubleshooting

### Java Version Error:
If you encounter issues related to the Java version, ensure that `JAVA_HOME` is correctly set in `properties.config`.

### Android SDK Not Found:
Ensure that `ANDROID_SDK_ROOT` is correctly set and that the SDK path contains necessary build tools.

### Artifact Not Found:
If an artifact is not found, verify that the GitHub repository exists and that the requested version tag is available.

## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.