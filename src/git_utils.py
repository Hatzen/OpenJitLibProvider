import os
import subprocess
from config import load_properties
from consts import LOCAL_CONFIG_FILE

config = load_properties(LOCAL_CONFIG_FILE)

def get_repo_url(targetHostUrl, organization, module):
    tokensByModule = config["REPOSITORY_TOKENS"]
    token = ""
    # get tokens for repos from config as well
    if (tokensByModule[module]):
        token = tokensByModule[module] + "@"
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
        print(f"Tag enthält SNAPSHOT. Wechsle zu Branch: {branch_name}")
        subprocess.run(['git', 'checkout', branch_name], check=True)
    else:
        try:
            run_command(['git', 'checkout', f'tags/{tag}'], cwd=repo_dir)
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