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

# When to use

Usually it is recommended to use a real maven nexus to host your artifacts. Some use public hosting some may prefer to have an onpremise nexus. 
Especially when it comes to open source libraries it is up to the repository owner if he is serving his artifacts in a public repo like maven central, google or in the past jcenter.
Some may not have published and abondomed there working project so it might be unethical to copy or fork the repo only to provide this artifacts.
That where JitPack comes in handy at least for side projects which have a small budget on hosting or providing libraries. It compiles all open source code "just in time" for libraries and snapshots very fine the last few years.

On the other hand jitpack is neither open source (except its docs) nor is completly clear if it financially stable enough to provide artifacts for the next few years. Espacially the number of open issues and the browndown of jcenter made it not to reliable. 
Therefore this repository shall provide a free and open source way to host artifacts locally and on premise as well it should integrate some migration to support old jcenter repos out of the box. Espacially by being open source it can be extended with cool functionality which is required by several providers.

## Features
- Clones GitHub repositories for specified modules and versions.
- Builds Android libraries (AAR files).
- Generates Maven metadata (POM files and SHA-1 hashes).
- Serves built artifacts and metadata through a Flask-based web server.

## Prerequisites
- Docker
OR
- Python 3.x
- pip
- Git
- Java (JDK 8 or 11 recommended)
- Android SDK

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

In the project root directory modify `config.yml` file so it will find the build tools required to build your libraries

## Usage

### Run the Flask Server:
```bash
python src/__init__.py
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

## Troubleshooting

### Artifact Not Found:
If an artifact is not found, verify that the GitHub repository exists and that the requested version tag is available.

## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.