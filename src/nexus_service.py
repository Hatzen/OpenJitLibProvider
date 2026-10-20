import os
import glob
import shutil
import base64
from datetime import datetime
from flask import send_file, abort, Response, request, render_template_string
from git_utils import (
    get_repo_url,
    clone_and_checkout,
    checkCommitHashAndUpdate,
    resolve_dynamic_version
)
from build_utils.build_wrapper import build
from build_utils.build_utils import (
    find_artifact_file,
    save_artifact,
    getPackagings
)
from maven_utils import (
    generate_maven_metadata,
    generate_pom_file,
    generate_sha1,
    generate_md5,
    write_checksums_for_file
)
from error_handler import log_method_output
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH
from config import get_config

def extract_auth_token_from_request():
    """Extracts token from HTTP Basic Authentication or Bearer header if provided."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return None

    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    if auth_header.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth_header[6:].strip()).decode('utf-8')
            # Format: username:password or token:password
            parts = decoded.split(':', 1)
            # If username is 'token' or similar, password contains token
            if len(parts) == 2:
                return parts[1] or parts[0]
            return decoded
        except Exception:
            pass

    return None

def handleRepositoryCall(artifact_path: str):
    """
    Main entry point for /repository/<artifact_path> requests.
    Supports single-module, multi-module, metadata, POMs, and checksum requests.
    """
    config = get_config()
    targetHostUrl = ""
    clean_path = artifact_path.strip("/")

    # If browsing repository root
    if not clean_path:
        return render_directory_index(LOCAL_REPO_PATH, "Repository Root")

    # Match host package prefix from KNOWN_HOSTS
    matched_prefix = None
    for hostPackage, hostUrl in config["KNOWN_HOSTS"].items():
        hostPackageUrl = hostPackage.replace(".", "/")
        if clean_path.startswith(hostPackageUrl + "/"):
            matched_prefix = hostPackageUrl
            targetHostUrl = hostUrl
            break
        elif clean_path == hostPackageUrl:
            matched_prefix = hostPackageUrl
            targetHostUrl = hostUrl
            break

    if not targetHostUrl:
        # Fallback check if path starts with com/github or similar known hosts
        abort(404, "No matching host found. Add one to KNOWN_HOSTS in config.")

    rel_path = clean_path[len(matched_prefix):].strip("/")
    parts = [p for p in rel_path.split('/') if p]

    # If browsing repository root or host directory
    if not parts:
        return render_directory_index(LOCAL_REPO_PATH, "Repository Root")

    # Determine organization, repo, module, version, filename
    # Cases:
    # 1. Root maven-metadata: [org, repo, 'maven-metadata.xml']
    # 2. Module maven-metadata: [org, repo, module, 'maven-metadata.xml']
    # 3. Standard release: [org, repo, version, file_name]
    # 4. Multi-module release: [org, repo, module, version, file_name]

    if len(parts) == 3 and parts[-1].startswith("maven-metadata.xml"):
        organization, repo = parts[0], parts[1]
        module = repo
        version = ""
        file_name = parts[-1]
    elif len(parts) == 4 and parts[-1].startswith("maven-metadata.xml"):
        organization, repo, module = parts[0], parts[1], parts[2]
        version = ""
        file_name = parts[-1]
    elif len(parts) == 4:
        organization, repo, version, file_name = parts[0], parts[1], parts[2], parts[3]
        module = repo
    elif len(parts) == 5:
        organization, repo, module, version, file_name = parts[0], parts[1], parts[2], parts[3], parts[4]
    else:
        # Check if requesting a directory listing
        dir_candidate = os.path.join(LOCAL_REPO_PATH, *parts)
        if os.path.isdir(dir_candidate):
            return render_directory_index(dir_candidate, f"Repository: {rel_path}")
        abort(400, f"Invalid artifact URL: {artifact_path}")

    auth_token = extract_auth_token_from_request()

    # Artifact directory path in repository storage
    if module and module != repo:
        artifact_dir = os.path.join(LOCAL_REPO_PATH, organization, repo, module, version)
    else:
        artifact_dir = os.path.join(LOCAL_REPO_PATH, organization, repo, version)

    target_file_path = os.path.join(artifact_dir, file_name)

    # 1. Handle Checksums (.sha1 / .md5)
    if file_name.endswith(".sha1") or file_name.endswith(".md5"):
        checksum_response = serve_or_compute_checksum(target_file_path)
        if checksum_response:
            return checksum_response

    # 2. If immutable release artifact already exists on disk, serve immediately
    if os.path.exists(target_file_path) and not ("SNAPSHOT" in version or "+" in version):
        return send_file(os.path.abspath(target_file_path))

    # 3. Otherwise execute or update build with error logging
    response = log_method_output(
        getArtifact,
        (targetHostUrl, organization, repo, module, version, file_name, artifact_dir, auth_token),
        {},
        organization,
        repo,
        module,
        version,
        file_name
    )

    if response:
        return response

    abort(404, f"Could not find or build artifact: {file_name}")

def serve_or_compute_checksum(target_checksum_path: str):
    """Serves checksum if available, or computes it from corresponding artifact if missing."""
    if os.path.exists(target_checksum_path):
        return send_file(os.path.abspath(target_checksum_path), mimetype="text/plain")

    # Determine base artifact file
    if target_checksum_path.endswith(".sha1"):
        base_file = target_checksum_path[:-5]
        if os.path.exists(base_file):
            hash_val = generate_sha1(base_file)
            return Response(hash_val + "\n", mimetype="text/plain")
    elif target_checksum_path.endswith(".md5"):
        base_file = target_checksum_path[:-4]
        if os.path.exists(base_file):
            hash_val = generate_md5(base_file)
            return Response(hash_val + "\n", mimetype="text/plain")

    return None

def getArtifact(targetHostUrl, organization, repo, module, version, file_name, artifact_dir, auth_token):
    """Handles fetching, checking out, building, and serving the requested artifact."""
    target_file_path = os.path.join(artifact_dir, file_name)

    # Build or fetch artifact
    built_path = handle_artifact_request(targetHostUrl, organization, repo, module, version, auth_token)

    if built_path and os.path.exists(built_path):
        # If the requested file is POM or checksum, check if it was generated
        if os.path.exists(target_file_path):
            return send_file(os.path.abspath(target_file_path))
        return send_file(os.path.abspath(built_path))

    if os.path.exists(target_file_path):
        return send_file(os.path.abspath(target_file_path))

    return None

def handle_artifact_request(targetHostUrl, organization, repo, module, version, auth_token=None):
    """Executes git clone, commit comparison, build, artifact saving, and rollback if build fails."""
    repo_url = get_repo_url(targetHostUrl, organization, repo, auth_token)

    # Resolve dynamic versions (Issue #14)
    if '+' in version or version.lower() == 'latest':
        resolved = resolve_dynamic_version(repo_url, version)
        print(f"Dynamic version resolved: {version} -> {resolved}")
        version = resolved

    # Directory for cloning and building
    clone_dir = os.path.join(LOCAL_CLONE_PATH, f"{repo}-{version}")
    os.makedirs(clone_dir, exist_ok=True)

    if module and module != repo:
        artifact_dest = os.path.join(LOCAL_REPO_PATH, organization, repo, module, version)
    else:
        artifact_dest = os.path.join(LOCAL_REPO_PATH, organization, repo, version)

    os.makedirs(artifact_dest, exist_ok=True)

    # Check if artifact already exists and commit hash has not changed
    needs_build = True
    commit_hash_file = os.path.join(artifact_dest, "gitCommitHash.txt")
    has_existing_artifacts = len(glob.glob(os.path.join(artifact_dest, "*.*"))) > 0

    if has_existing_artifacts:
        # For non-snapshots with existing build, no rebuild needed
        if not ("SNAPSHOT" in version):
            print(f"Artifact already built and cached in {artifact_dest}")
            existing = find_artifact_file(artifact_dest, module)
            if existing:
                return existing[0]

    # Backup existing artifacts for rollback if rebuild fails (Issue #19)
    backup_dir = None
    if has_existing_artifacts and "SNAPSHOT" in version:
        backup_dir = os.path.join(LOCAL_CLONE_PATH, f"backup-{repo}-{version}")
        try:
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            shutil.copytree(artifact_dest, backup_dir)
        except Exception as e:
            print(f"Failed to create rollback backup: {e}")

    try:
        print(f"Cloning / updating {repo_url} (version: {version})")
        clone_and_checkout(repo_url, version, clone_dir)

        # Check commit hash for snapshot updates
        needs_build = checkCommitHashAndUpdate(clone_dir, artifact_dest, repo_url=repo_url, version=version)
        if not needs_build and has_existing_artifacts:
            print("Commit hash unchanged. Serving existing cached artifact.")
            existing = find_artifact_file(artifact_dest, module)
            if existing:
                return existing[0]

        print(f"Building project {repo} (module: {module})...")
        build(clone_dir, target_module=module if module != repo else None)

        print("Searching for built artifacts...")
        artifact_files = find_artifact_file(clone_dir, module=module if module != repo else None)
        print(f"Discovered artifact files: {artifact_files}")

        if artifact_files:
            dest_file = save_artifact(artifact_files, organization, module, version, dest_dir=artifact_dest)
            packaging = getPackagings(artifact_files)

            # Generate Maven metadata & POM
            group_id = f"{targetHostUrl.split('.')[0]}.{organization}" if '.' in targetHostUrl else f"com.github.{organization}"
            generate_maven_metadata(group_id, module, version, repo_base_path=os.path.dirname(artifact_dest))
            generate_pom_file(group_id, module, version, packaging=packaging, artifact_dir=artifact_dest)

            # Cleanup backup on successful build
            if backup_dir and os.path.exists(backup_dir):
                shutil.rmtree(backup_dir, ignore_errors=True)

            print(f"Successfully saved and indexed: {dest_file}")
            return dest_file

        raise Exception(f"No built artifact files (.jar / .aar / .war) found in {clone_dir}")

    except Exception as e:
        print(f"Build failed for {organization}/{repo}/{module}/{version}: {e}")
        # Rollback to previous working snapshot build if available (Issue #19)
        if backup_dir and os.path.exists(backup_dir):
            print(f"Rolling back snapshot to previous build from {backup_dir}")
            try:
                for item in os.listdir(backup_dir):
                    s = os.path.join(backup_dir, item)
                    d = os.path.join(artifact_dest, item)
                    if os.path.isfile(s):
                        shutil.copy2(s, d)
                shutil.rmtree(backup_dir, ignore_errors=True)
                existing = find_artifact_file(artifact_dest, module)
                if existing:
                    return existing[0]
            except Exception as rollback_err:
                print(f"Rollback failed: {rollback_err}")
        raise

def render_directory_index(directory_path: str, title: str):
    """Renders a standard clean Apache/Nexus directory index page."""
    items = []
    if os.path.exists(directory_path):
        for entry in sorted(os.listdir(directory_path)):
            full = os.path.join(directory_path, entry)
            is_dir = os.path.isdir(full)
            size = os.path.getsize(full) if not is_dir else "-"
            mtime = os.path.getmtime(full)
            time_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S') if 'datetime' in globals() else ""
            items.append({
                "name": entry + ("/" if is_dir else ""),
                "is_dir": is_dir,
                "size": size,
                "mtime": time_str
            })

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Index of {title}</title>
    <style>
        body {{ font-family: monospace; padding: 24px; background: #fafafa; color: #333; }}
        h1 {{ font-size: 20px; border-bottom: 1px solid #ddd; padding-bottom: 8px; }}
        table {{ border-collapse: collapse; width: 100%; max-width: 900px; }}
        th, td {{ text-align: left; padding: 6px 12px; }}
        tr:hover {{ background: #f0f0f0; }}
        a {{ text-decoration: none; color: #0366d6; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Index of {title}</h1>
    <table>
        <tr><th>Name</th><th>Size</th></tr>
        {"".join(f'<tr><td><a href="{item["name"]}">{item["name"]}</a></td><td>{item["size"]}</td></tr>' for item in items)}
    </table>
</body>
</html>"""
    return Response(html, mimetype="text/html")