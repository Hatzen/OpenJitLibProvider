import os
import subprocess
from config import load_properties
from consts import LOCAL_CONFIG_FILE

# TODO: Fullfill and pass as argument
providers = ["https://github.com/", "https://gitlab.com/"]

def get_repo_url(organization, module, provider = "github"):
    
    tokensByModule = load_properties(LOCAL_CONFIG_FILE)["REPOSITORY_TOKENS"]
    # providers.append(config.getCustomProviders)
    token = ""
    # get tokens for repos from config as well
    if (tokensByModule[module]):
        token = tokensByModule[module] + "@"
    return f"https://{token}github.com/{organization}/{module}.git"

def clone_and_checkout(repo_url, version, clone_dir):
    if not os.listdir(clone_dir):
        subprocess.run(["git", "clone", repo_url, clone_dir], check=True)
    if version != "master":
        checkout_tag(clone_dir, version)

def checkout_tag(repo_dir, tag):
    # TODO: Check tag for -SNAPSHOT postfix and use branch instead of tag.
    try:
        run_command(['git', 'checkout', f'tags/{tag}'], cwd=repo_dir)
    except subprocess.CalledProcessError:
        run_command(['git', 'checkout', f'tags/v{tag}'], cwd=repo_dir)

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