import os
import subprocess
from config import load_properties
from consts import LOCAL_CONFIG_FILE

config = load_properties(LOCAL_CONFIG_FILE)

def get_repo_url(targetHostUrl, organization, module):
    tokensByModule = config.get("REPOSITORY_TOKENS")
    token = ""
    # get tokens for repos from config as well
    tokenForModule = tokensByModule.get(module)
    if (tokenForModule):
        token = tokenForModule + "@"
    return f"https://{token}{targetHostUrl}/{organization}/{module}.git"

def clone_and_checkout(repo_url, version, clone_dir):
    if not os.listdir(clone_dir):
        subprocess.run(["git", "clone", repo_url, clone_dir], check=True)
    checkout_tag(clone_dir, version)

def checkout_tag(repo_dir, tag):
    # Check if tag exists. Not working properly, so remove.
    #try:
    #    subprocess.run(['git', 'rev-parse', tag_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #except subprocess.CalledProcessError:
    #    print(f"Tag oder Branch {tag_name} existiert nicht.")
    #    return

    if '-SNAPSHOT' in tag:
        # Convert SNAPSHOT tag to branch name
        branch_name = tag.replace('-SNAPSHOT', '')
        print(f"Tag contains SNAPSHOT. Switch to branch: {branch_name}")
        subprocess.run(['git', 'checkout', branch_name], check=True)
    else:
        try:
            try:
                run_command(['git', 'checkout', f'tags/{tag}'], cwd=repo_dir)
            except subprocess.CalledProcessError:
                run_command(['git', 'checkout', f'tags/v{tag}'], cwd=repo_dir)
        except subprocess.CalledProcessError:
            # If it is commit hash.
            run_command(['git', 'checkout', tag], cwd=repo_dir)

def run_command(command, cwd=None):
    try:
        result = subprocess.run(
            command,
            cwd=cwd, 
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("Command Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command {command} failed with error: {e}")
        raise



def checkCommitHashAndUpdate(clone_dir, repo_dir):
    commit_hash_path = os.path.join(repo_dir, 'gitCommitHash.txt')
    
    if not os.path.exists(commit_hash_path):
        os.makedirs(repo_dir, exist_ok=True)
    current_hash = get_current_commit_hash(clone_dir)

    if current_hash is None:
        print("Could not determine hash.")
        return

    saved_hash = read_saved_commit_hash(commit_hash_path)

    if saved_hash is None:
        print("No saved commit hash found. Writing the current hash to file.")
        write_commit_hash(commit_hash_path, current_hash)
        return True
    elif current_hash != saved_hash:
        print("Commit hash has changed. Updating the repository.")
        git_update()
        write_commit_hash(commit_hash_path, current_hash)
        return True
    else:
        print("Commit hash is the same. No update needed.")
    return False


def get_current_commit_hash(clone_dir):
    try:
        print(clone_dir)
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=clone_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error while getting current commit hash: {e}")
        return None

def read_saved_commit_hash(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

def write_commit_hash(file_path, commit_hash):
    with open(file_path, 'w') as file:
        file.write(commit_hash)

def git_update():
    try:
        subprocess.run(['git', 'pull'], check=True)
        print("Repository updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error while updating repository: {e}")