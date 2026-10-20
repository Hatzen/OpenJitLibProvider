# 🚀 OpenJitLibProvider

**OpenJitLibProvider** is a fast, open-source, on-premise Maven repository proxy designed to **completely replace JitPack**. It automatically clones, builds, caches, and serves artifacts on-the-fly directly from **GitHub, GitLab, Bitbucket, Gitee, Azure DevOps**, or your own private Git servers.

---

## 🌟 Why OpenJitLibProvider?

| Feature | JitPack | OpenJitLibProvider |
| :--- | :--- | :--- |
| **Open Source** | ❌ Proprietary (Docs only) | ✅ 100% Free & Open Source (MIT) |
| **On-Premise / Self-Hosted** | ❌ Paid enterprise only | ✅ Native (Docker & Python) |
| **Multi-Module Gradle / Maven** | ✅ Supported | ✅ Fully Supported |
| **Defunct JCenter Auto-Fix** | ❌ Fails on missing JCenter artifacts | ✅ Automatic migration to Maven Central & Google |
| **Legacy Gradle Wrapper Upgrades** | ❌ Fails on Gradle 1.x - 3.x | ✅ Auto-upgraded to Gradle 4.1-all |
| **Private Repositories & Tokens** | ❌ Requires credentials upload | ✅ Secure local token or HTTP Basic Auth |
| **Multi-Git Host Support** | ✅ GitHub, GitLab, Bitbucket | ✅ GitHub, GitLab, Bitbucket, Gitee, Azure, Custom |
| **Web UI & Build Logs** | ⚠️ Basic web page | ✅ Built-in Web Dashboard, Log Viewer & Stats |
| **Snapshot Rebuilds & Rollback** | ⚠️ May leave broken builds | ✅ Hash change detection + Automatic Rollback |
| **Offline / Air-Gapped Cache** | ❌ No | ✅ Persistent local storage of built artifacts |

---

## 📋 Table of Contents
1. [Quick Start with Docker](#quick-start-with-docker)
2. [Local Installation](#local-installation)
3. [Client Configuration (Gradle & Maven)](#client-configuration)
   - [Gradle Setup (build.gradle)](#gradle-setup)
   - [Kotlin DSL (build.gradle.kts)](#kotlin-dsl)
   - [Maven Setup (pom.xml)](#maven-setup)
4. [Supported Dependency Formats](#supported-dependency-formats)
   - [Single Module](#single-module)
   - [Multi-Module Projects](#multi-module-projects)
   - [Branches & SNAPSHOTs](#branches--snapshots)
   - [Dynamic Versions](#dynamic-versions)
5. [Private Repositories & Authentication](#private-repositories--authentication)
6. [Supported Git Hosts](#supported-git-hosts)
7. [Supported Gradle & Java Versions](#supported-gradle--java-versions)
8. [Automatic JCenter & Legacy Migration](#automatic-jcenter-migration)
9. [Web Dashboard & REST API](#web-dashboard--rest-api)
10. [Configuration Reference](#configuration-reference)

---

## 🐳 Quick Start with Docker

The fastest way to deploy OpenJitLibProvider is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/Hatzen/OpenJitLibProvider.git
cd OpenJitLibProvider

# Start server
docker compose up -d
```

Open your browser at `http://localhost:5000` to access the interactive web dashboard.

---

## 💻 Local Installation

### Prerequisites
- Python 3.9+
- Git 2.20+
- Java (JDK 8, 11, 17, or 21)
- Android SDK (optional, required only for Android `.aar` library builds)

### Installation Steps
```bash
git clone https://github.com/Hatzen/OpenJitLibProvider.git
cd OpenJitLibProvider

# Install Python requirements
pip install -r requirements.txt

# Copy and edit local configuration
cp config-local-example.yml config.yml

# Start OpenJitLibProvider
python src/__init__.py
```

---

## 🛠️ Client Configuration

### Gradle Setup (`build.gradle`)

> [!TIP]
> **Repository Ordering Best Practice**: Always place `mavenCentral()` and `google()` **above** OpenJitLibProvider. This ensures standard public dependencies resolve quickly, while custom Git libraries fall through to OpenJitLibProvider.

```groovy
repositories {
    google()
    mavenCentral()
    maven {
        url 'http://localhost:5000/repository'
        allowInsecureProtocol = true // required if using HTTP instead of HTTPS
    }
}

// Recommended for SNAPSHOT builds to check for updates frequently
configurations.all {
    resolutionStrategy.cacheChangingModulesFor 0, 'seconds'
}

dependencies {
    // Standard library build
    implementation 'com.github.User:Repo:1.0.0'

    // Multi-module build
    implementation 'com.github.User:Repo:submodule:1.0.0'

    // Branch snapshot
    implementation 'com.github.User:Repo:master-SNAPSHOT'
}
```

### Kotlin DSL (`build.gradle.kts`)

```kotlin
repositories {
    google()
    mavenCentral()
    maven {
        url = uri("http://localhost:5000/repository")
        isAllowInsecureProtocol = true
    }
}
```

### Maven Setup (`pom.xml`)

```xml
<repositories>
    <repository>
        <id>openjit-repo</id>
        <name>OpenJitLibProvider</name>
        <url>http://localhost:5000/repository</url>
    </repository>
</repositories>

<dependencies>
    <dependency>
        <groupId>com.github.User</groupId>
        <artifactId>Repo</artifactId>
        <version>1.0.0</version>
    </dependency>
</dependencies>
```

---

## 📦 Supported Dependency Formats

### Single Module
- **Tag:** `com.github.User:Repo:1.2.3`
- **v-prefix Tag:** `com.github.User:Repo:v1.2.3`
- **Commit Hash:** `com.github.User:Repo:a1b2c3d`

### Multi-Module Projects
For repositories containing multiple submodules:
- `com.github.User:Repo:submodule:1.0.0`
- `com.github.User.Repo:submodule:1.0.0`

OpenJitLibProvider runs `:submodule:assembleRelease` or `:submodule:build` and isolates the submodule's artifacts.

### Branches & SNAPSHOTs
- Branch build: `com.github.User:Repo:master-SNAPSHOT` or `main-SNAPSHOT`
- OpenJitLibProvider checks the remote git commit hash via `git ls-remote`. If the branch has new commits, it fetches the changes and builds a fresh snapshot.
- If a snapshot build fails, OpenJitLibProvider automatically **rolls back** to the previously working snapshot build so your builds don't break.

### Dynamic Versions
- Range / wildcard versions: `com.github.User:Repo:1.0.+` or `1.+`
- Latest tag: `com.github.User:Repo:latest`

OpenJitLibProvider queries all git tags remotely and resolves the highest matching semantic version.

---

## 🔐 Private Repositories & Authentication

### Option 1: HTTP Basic Auth in Gradle/Maven (Recommended)
You can supply access tokens in Gradle credentials:
```groovy
repositories {
    maven {
        url 'http://localhost:5000/repository'
        credentials {
            username = "token"
            password = "\${System.env.GITHUB_TOKEN}"
        }
    }
}
```

### Option 2: Server-side `config.yml`
```yaml
REPOSITORY_TOKENS:
  "default": "ghp_global_fallback_token"
  "MyOrg/PrivateRepo": "ghp_specific_repo_token"
```

### Option 3: Environment Variable
```bash
export GITHUB_TOKEN=ghp_your_personal_access_token
```

---

## 🌐 Supported Git Hosts

Configure known hosts in `config.yml`:

| Host Prefix | Git Host | Example Coordinate |
| :--- | :--- | :--- |
| `com.github` | `github.com` | `com.github.User:Repo:Tag` |
| `com.gitlab` | `gitlab.com` | `com.gitlab.User:Repo:Tag` |
| `org.bitbucket` | `bitbucket.org` | `org.bitbucket.User:Repo:Tag` |
| `com.gitee` | `gitee.com` | `com.gitee.User:Repo:Tag` |
| `com.azure` | `dev.azure.com` | `com.azure.User:Repo:Tag` |

Custom hosts can be added in `config.yml` under `KNOWN_HOSTS`.

---

## ☕ Supported Gradle & Java Versions

OpenJitLibProvider automatically detects the Gradle or Maven version of target repositories and selects the optimal Java compiler runtime:

| Gradle Wrapper Version | Compatible Java Runtimes |
| :--- | :--- |
| **Gradle 8.5 – 8.10+** | Java 17, Java 21 |
| **Gradle 7.3 – 8.4** | Java 11, Java 17 |
| **Gradle 6.0 – 7.2** | Java 8, Java 11, Java 17 |
| **Gradle 5.0 – 5.6** | Java 8, Java 11 |
| **Gradle 4.0 – 4.10** | Java 7, Java 8 |
| **Gradle 1.x – 3.x** | *Auto-upgraded to Gradle 4.1-all* |

---

## 🔄 Automatic JCenter & Legacy Migration

Because JCenter and Bintray were shut down, many open-source libraries from 2015–2020 fail to build on standard servers. OpenJitLibProvider automatically patches build files during checkout:
- Replaces `jcenter()` repository declarations with `mavenCentral()` + Google repository.
- Removes obsolete plugins: `com.novoda:bintray-release` and `com.jfrog.bintray.gradle:gradle-bintray-plugin`.
- Upgrades legacy `com.android.tools.build:gradle:2.x` to `3.0.0`.
- Elevates obsolete Gradle 1.x / 2.x / 3.x wrappers to `gradle-4.1-all.zip`.

---

## 📊 Web Dashboard & REST API

OpenJitLibProvider includes a web dashboard and monitoring API:

| URL | Description |
| :--- | :--- |
| `/` | Interactive Web Dashboard (storage, counts, quick actions) |
| `/list` | Artifacts File Browser & Direct Downloads |
| `/logs` | Build Logs Viewer with in-browser formatting |
| `/repository/` | Standard Apache/Nexus style repository directory index |
| `/api/stats` | JSON Status & Storage Metrics API |
| `/api/reload_config` | Hot-reload `config.yml` without restarting the server |
| `/cleanup/run` | Trigger disk space cleanup immediately |
| `/refresh/<artifact>` | Force re-cloning and re-building of a specific artifact |
| `/clear/cache` | Delete temporary build files (`tmp/`) |
| `/clear/logs` | Delete build log files (`logs/`) |
| `/clear/all` | Delete all temporary, log, and cached repository files |

---

## ⚙️ Configuration Reference (`config.yml`)

```yaml
# Port to run OpenJitLibProvider server
NEXUS_PORT: 5000

# JDK Paths mapping
JAVA_HOME:
  "8": "C:/Program Files/Java/jdk-8"
  "11": "C:/Program Files/Java/jdk-11"
  "17": "C:/Program Files/Java/jdk-17"
  "21": "C:/Program Files/Java/jdk-21"

# Android SDK Path
ANDROID_SDK_ROOT: "C:/Users/user/AppData/Local/Android/Sdk"

# Git Host Mappings
KNOWN_HOSTS:
  "com.github": "github.com"
  "com.gitlab": "gitlab.com"
  "org.bitbucket": "bitbucket.org"
  "com.gitee": "gitee.com"
  "com.azure": "dev.azure.com"

# Private repository access tokens
REPOSITORY_TOKENS:
  "default": ""
  "User/PrivateRepo": "ghp_xxxx"

# Automated cleanup schedule in days (-1 to disable)
DELETE_ARTIFACTS: -1   # Expire cached artifacts unused for N days
DELETE_TMP: 1          # Delete build working directories older than N days
```

---

## 📄 License
Licensed under the [MIT License](LICENSE).