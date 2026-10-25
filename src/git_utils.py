import os
import re
import subprocess
from config import get_config

def get_token_for_repo(organization: str, repo: str, explicit_token: str = None) -> str:
    """Finds authentication token from explicit parameter, config, or environment variables."""
    if explicit_token:
        return explicit_token

    config = get_config()
    tokens = config.get("REPOSITORY_TOKENS") or {}

    # Check exact match "org/repo"
    key_full = f"{organization}/{repo}"
    if key_full in tokens:
        return str(tokens[key_full])
    
    # Check repo or module name
    if repo in tokens:
        return str(tokens[repo])

    # Check organization
    if organization in tokens:
        return str(tokens[organization])

    # Check default token in config
    if "default" in tokens:
        return str(tokens["default"])

    # Check environment variables
    env_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GIT_TOKEN")
    if env_token:
        return env_token

    return ""

def get_repo_url(targetHostUrl: str, organization: str, repo: str, token: str = None) -> str:
    """Builds git clone URL, supporting private repositories with authentication tokens."""
    token = get_token_for_repo(organization, repo, token)
    auth_prefix = f"{token}@" if token else ""
    return f"https://{auth_prefix}{targetHostUrl}/{organization}/{repo}.git"

def run_git(args, cwd=None, check=True, text=True):
    """Executes a git command safely across Windows and Linux without shell injection."""
    cmd = ["git"] + list(args)
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=text,
        check=check
    )
    return result

def resolve_dynamic_version(repo_url: str, version_pattern: str) -> str:
    """
    Resolves dynamic versions such as '1.0.+', '1.+', '+', or 'latest'
    by querying git ls-remote tags and selecting the highest matching semantic version.
    """
    if not ('+' in version_pattern or version_pattern.lower() == 'latest'):
        return version_pattern

    try:
        res = run_git(["ls-remote", "--tags", repo_url], check=False)
        if res.returncode != 0:
            return version_pattern

        tags = []
        for line in res.stdout.splitlines():
            # line format: <hash>\trefs/tags/<tag>
            parts = line.strip().split("\t")
            if len(parts) >= 2 and "refs/tags/" in parts[1]:
                tag = parts[1].replace("refs/tags/", "")
                if not tag.endswith("^{}"):  # exclude peeled tags
                    tags.append(tag)

        if not tags:
            return version_pattern

        # Filter tags by pattern
        prefix = version_pattern.rstrip("+").rstrip(".")
        matching = []
        for tag in tags:
            clean_tag = tag.lstrip("v")
            if version_pattern.lower() == "latest" or not prefix:
                matching.append(tag)
            elif clean_tag.startswith(prefix) or tag.startswith(prefix):
                matching.append(tag)

        if not matching:
            return version_pattern

        # Natural / semantic version sort
        def version_key(t):
            raw = t.lstrip("v")
            parts = re.split(r'[-._]', raw)
            key = []
            for p in parts:
                if p.isdigit():
                    key.append((0, int(p)))
                else:
                    key.append((1, p))
            return key

        matching.sort(key=version_key)
        return matching[-1]
    except Exception as e:
        print(f"Error resolving dynamic version {version_pattern}: {e}")
        return version_pattern

def get_remote_head_commit(repo_url: str, branch_name: str) -> str:
    """Retrieves the latest commit hash from the remote branch."""
    try:
        res = run_git(["ls-remote", repo_url, f"refs/heads/{branch_name}"], check=False)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.split()[0].strip()
        # Fallback to HEAD
        res_head = run_git(["ls-remote", repo_url, "HEAD"], check=False)
        if res_head.returncode == 0 and res_head.stdout.strip():
            return res_head.stdout.split()[0].strip()
    except Exception as e:
        print(f"Failed to query remote commit for {repo_url} {branch_name}: {e}")
    return ""

def clone_and_checkout(repo_url: str, version: str, clone_dir: str):
    """Clones repository if not cloned, fetches updates, and checks out specified tag/branch/commit."""
    if not os.path.exists(os.path.join(clone_dir, ".git")):
        os.makedirs(clone_dir, exist_ok=True)
        print(f"Cloning {repo_url} into {clone_dir}")
        run_git(["clone", repo_url, clone_dir])
    else:
        # Fetch remote updates
        try:
            run_git(["fetch", "--all", "--tags"], cwd=clone_dir, check=False)
        except Exception as e:
            print(f"Fetch failed: {e}")

    checkout_tag(clone_dir, version)

def checkout_tag(repo_dir: str, tag: str):
    """Checks out tag, branch, or commit hash with fallbacks."""
    if '-SNAPSHOT' in tag:
        branch_name = tag.replace('-SNAPSHOT', '')
        print(f"Tag contains SNAPSHOT. Switching to branch: {branch_name}")
        # Try local or remote tracking branch
        try:
            run_git(['checkout', branch_name], cwd=repo_dir)
            run_git(['pull', 'origin', branch_name], cwd=repo_dir, check=False)
        except subprocess.CalledProcessError:
            try:
                run_git(['checkout', '-B', branch_name, f'origin/{branch_name}'], cwd=repo_dir)
            except subprocess.CalledProcessError:
                run_git(['checkout', tag], cwd=repo_dir)
        return

    # Try tags/tag
    try:
        run_git(['checkout', f'tags/{tag}'], cwd=repo_dir)
        return
    except subprocess.CalledProcessError:
        pass

    # Try tags/v{tag}
    try:
        run_git(['checkout', f'tags/v{tag}'], cwd=repo_dir)
        return
    except subprocess.CalledProcessError:
        pass

    # Try tags without 'v' if tag started with 'v'
    if tag.startswith('v') and len(tag) > 1:
        try:
            run_git(['checkout', f'tags/{tag[1:]}'], cwd=repo_dir)
            return
        except subprocess.CalledProcessError:
            pass

    # Try branch directly
    try:
        run_git(['checkout', tag], cwd=repo_dir)
        return
    except subprocess.CalledProcessError:
        pass

    # Try remote branch
    try:
        run_git(['checkout', f'origin/{tag}'], cwd=repo_dir)
        return
    except subprocess.CalledProcessError:
        pass

    # Finally try commit hash or direct rev
    run_git(['checkout', tag], cwd=repo_dir)

def checkCommitHashAndUpdate(clone_dir: str, artifact_dir: str, repo_url: str = None, version: str = None) -> bool:
    """
    Checks if repository commit hash has changed. For snapshots, checks remote hash.
    Returns True if rebuild is needed, False otherwise.
    """
    commit_hash_path = os.path.join(artifact_dir, 'gitCommitHash.txt')
    os.makedirs(artifact_dir, exist_ok=True)
    
    saved_hash = read_saved_commit_hash(commit_hash_path)

    # For snapshot versions, check if remote branch has a new commit
    if version and '-SNAPSHOT' in version and repo_url:
        branch_name = version.replace('-SNAPSHOT', '')
        remote_hash = get_remote_head_commit(repo_url, branch_name)
        if remote_hash and saved_hash:
            if remote_hash != saved_hash:
                print(f"Snapshot remote hash changed ({saved_hash} -> {remote_hash}). Rebuild required.")
                return True
            else:
                return False

    current_hash = get_current_commit_hash(clone_dir)
    if current_hash is None:
        return True

    if saved_hash is None:
        write_commit_hash(commit_hash_path, current_hash)
        return True
    elif current_hash != saved_hash:
        write_commit_hash(commit_hash_path, current_hash)
        return True

    return False

def get_current_commit_hash(clone_dir: str):
    try:
        result = run_git(['rev-parse', 'HEAD'], cwd=clone_dir)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error while getting current commit hash: {e}")
        return None

def read_saved_commit_hash(file_path: str):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except (FileNotFoundError, IOError):
        return None

def write_commit_hash(file_path: str, commit_hash: str):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(commit_hash)
    except IOError as e:
        print(f"Error saving commit hash: {e}")

def git_update(clone_dir: str = None):
    try:
        run_git(['pull'], cwd=clone_dir)
        print("Repository updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error while updating repository: {e}")