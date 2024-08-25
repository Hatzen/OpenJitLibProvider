import os
import sys
import subprocess
import shutil
from glob import glob


def read_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return [line.strip() for line in lines]

def run_command(command, cwd=None):
    try:
        subprocess.run(command, cwd=cwd, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Command {command} failed with error: {e}")

def clone_repo(repo_url, clone_dir):
    run_command(['git', 'clone', repo_url, clone_dir])

def checkout_tag(repo_dir, tag):
    try:
        run_command(['git', 'checkout', f'tags/{tag}'], cwd=repo_dir)
    except:
        run_command(['git', 'checkout', f'tags/v{tag}'], cwd=repo_dir)

def set_java_home(java_home_path):
    os.environ['JAVA_HOME'] = java_home_path
    os.environ['PATH'] = java_home_path + "\\bin;" + os.environ['PATH']

def enforce_groovy_version(repo_dir, groovy_version="3.0.9"):
    build_gradle_path = os.path.join(repo_dir, 'build.gradle')

    if os.path.exists(build_gradle_path):
        with open(build_gradle_path, 'a') as file:
            file.write(f"\nconfigurations.all {{\n    resolutionStrategy.force 'org.codehaus.groovy:groovy-all:{groovy_version}'\n}}\n")

def build_with_gradle(repo_dir):
    # update_gradle_wrapper(repo_dir)  # Update Gradle wrapper before building
    # enforce_groovy_version(repo_dir)  # Enforce a compatible Groovy version
    run_command(['gradlew.bat', 'assembleRelease'], cwd=repo_dir)

def prepare_ivy_package(repo_dir, group, name, version, ivy_repo_dir):
    ivy_file_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<ivy-module version="2.0">
    <info organisation="{group}"
          module="{name}"
          revision="{version}"/>
    <publications>
        <artifact name="{name}" type="aar" ext="aar"/>
    </publications>
</ivy-module>
"""
    ivy_file_path = os.path.join(repo_dir, 'ivy.xml')
    with open(ivy_file_path, 'w') as ivy_file:
        ivy_file.write(ivy_file_content)
    
    ivy_dest_dir = os.path.join(ivy_repo_dir, group.replace('.', '/'), name, version)
    os.makedirs(ivy_dest_dir, exist_ok=True)
    
    # aar_files = [f for f in os.listdir(os.path.join(repo_dir, 'build', 'outputs', 'aar')) if f.endswith('.aar')]
    aar_files = []
    for filename in glob(repo_dir + '/**/*.aar', recursive=True):
        print(filename)
        aar_files.append(filename)
    print("finished files")

    for aar_file in aar_files:
        shutil.copy(aar_file, ivy_dest_dir)
    
    shutil.copy(ivy_file_path, ivy_dest_dir)

def process_line(line, base_dir, ivy_repo_dir, java_home_path):
    parts = line.split(':')
    if len(parts) != 3:
        print(f"Invalid line format: {line}")
        return

    group, name, version = parts
    group = group.replace('com.github.', '')
    repo_url = f"https://github.com/{group.replace('.', '/')}/{name}.git"
    clone_dir = os.path.join(base_dir, name)

    try:
        clone_repo(repo_url, clone_dir)
        checkout_tag(clone_dir, version)
        set_java_home(java_home_path)
        build_with_gradle(clone_dir)
        prepare_ivy_package(clone_dir, group, name, version, ivy_repo_dir)
    except Exception as e:
        print(f"Error processing {line}: {e}")
    finally:
        if os.path.exists(clone_dir):
            sys.stdout.flush() 
            # shutil.rmtree(clone_dir)

def main(file_path, base_dir, ivy_repo_dir, java_home_path):
    lines = read_file(file_path)
    for line in lines:
        process_line(line, base_dir, ivy_repo_dir, java_home_path)

if __name__ == "__main__":
    file_path = "dependencies.txt"  # Pfad zur Datei mit den Abhängigkeiten
    base_dir = "temp/github_projects"  # Temporäres Verzeichnis für die Repositories
    ivy_repo_dir = "ivy/repo"  # Zielverzeichnis für das Ivy-Repository
    # TODO: To support more gradle wrappers use jdk 1.8
    java_home_path = "C:/Program Files/Java/jdk-11.0.2/"  # Setze den Pfad zu deiner Java-Installation
    os.environ['ANDROID_SDK_ROOT'] = "C:/Users/kaiha/AppData/Local/Android/Sdk"

    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(ivy_repo_dir, exist_ok=True)

    main(file_path, base_dir, ivy_repo_dir, java_home_path)