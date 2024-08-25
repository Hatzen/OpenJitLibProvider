import os
import subprocess

def clone_and_checkout(repo_url, version, clone_dir):
    if not os.listdir(clone_dir):
        subprocess.run(["git", "clone", repo_url, clone_dir], check=True)
    if version != "master":
        checkout_tag(clone_dir, version)

def checkout_tag(repo_dir, tag):
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