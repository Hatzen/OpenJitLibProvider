import os
import sys
import subprocess
from glob import glob
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH
import xml.etree.ElementTree as ET
import re

# sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def detect_project_type(folder):
    """Detect if the folder is a Maven or Gradle project based on the presence of key files."""
    if os.path.exists(os.path.join(folder, 'pom.xml')):
        return 'maven'
    elif os.path.exists(os.path.join(folder, 'build.gradle')) or os.path.exists(os.path.join(folder, 'settings.gradle')):
        return 'gradle'
    else:
        return 'unknown'
    

def find_artifact_file(clone_dir):
    extensions_to_find = ['.war', '.jar', '.aar'] 
    return find_files_with_extensions(clone_dir, extensions_to_find)
    # filepaths = []
    # # build_path = os.path.join(clone_dir, 'build', '**')
    # build_path = os.path.join(clone_dir, 'build')
    # for filename in glob(os.path.join(build_path, '*.aar'), recursive=True):
    #     print(f"Found AAR file: {filename}")
    #     filepaths.append(filename)
    # for filename in glob(os.path.join(build_path, '*.jar'), recursive=True):
    #     print(f"Found jar file: {filename}")
    #     filepaths.append(filename)
    # for filename in glob(os.path.join(build_path, '*.war'), recursive=True):
    #     print(f"Found war file: {filename}")
    #     filepaths.append(filename)
    # return filepaths


def find_files_with_extensions(root_dir, extensions):
    valid_artefact_dirs = ['libs', 'outputs'] # 'build' in dirpath

    found_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        if any(artefact_dir in dirpath for artefact_dir in valid_artefact_dirs):
            for file in filenames:
                # Prüfe, ob die Datei eine der angegebenen Endungen hat
                if any(file.endswith(ext) for ext in extensions):
                    found_files.append(os.path.join(dirpath, file))
    
    return found_files

def save_artifact(artifact_files, organization, module, version):
    dest_dir = getArtifactDest(organization, module, version)
    os.makedirs(dest_dir, exist_ok=True)
    for artifact in artifact_files:
        ending = getEnding(artifact)
        dest_file = os.path.join(dest_dir, f"{module}-{version}{ending}")
        print("saving artifact")
        print(artifact + " " + dest_file)
        if os.path.exists(dest_file):
            os.remove(dest_file)
        os.rename(artifact, dest_file)
    return dest_file

def getPackagings(artifact_files):
    packagings = []
    for artifact in artifact_files:
        packageing = getEnding(artifact).replace("\.", "")
        packagings.append(packageing)
    return packageing

def getArtifactDest(organization, repo, version):
    group_path = organization.replace('.', '/')
    dest_dir = os.path.join(LOCAL_REPO_PATH, group_path, repo, version)
    return dest_dir

def getEnding(artifact):
    return os.path.splitext(artifact)[-1]


def remove_line_with_partial_match(file_path, match_string):
    replace_line_with_partial_match(file_path, match_string, "")

def replace_line_with_partial_match(file_path, match_string, replacement_string):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        new_lines = [replacement_string if match_string in line else line for line in lines]
        with open(file_path, 'w') as file:
            file.writelines(new_lines)
    except:
        # print('could not replace', file_path, old_line, new_line)
        pass

def replace_in_file(file_path, old_line, new_line):
    try:
        with open(file_path, 'r') as file:
            content = file.read().replace(old_line, new_line)
        with open(file_path, 'w') as file:
            file.write(content)
    except:
        # print('could not replace', file_path, old_line, new_line)
        pass
