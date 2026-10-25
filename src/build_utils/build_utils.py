import os
import sys
import shutil
import hashlib
from consts import LOCAL_REPO_PATH

def detect_project_type(folder):
    """Detect if the folder is a Maven or Gradle project based on the presence of key files."""
    if os.path.exists(os.path.join(folder, 'pom.xml')):
        return 'maven'
    elif (os.path.exists(os.path.join(folder, 'build.gradle')) or 
          os.path.exists(os.path.join(folder, 'build.gradle.kts')) or
          os.path.exists(os.path.join(folder, 'settings.gradle')) or
          os.path.exists(os.path.join(folder, 'settings.gradle.kts'))):
        return 'gradle'
    else:
        return 'unknown'

def find_artifact_file(clone_dir, module=None):
    """Finds built artifacts, prioritizing module subfolder if module is specified."""
    extensions_to_find = ['.aar', '.jar', '.war', '.zip', '.module']
    
    # If module is specified, look inside module directory first
    if module:
        module_dir = os.path.join(clone_dir, module.replace(":", os.sep))
        if os.path.exists(module_dir):
            files = find_files_with_extensions(module_dir, extensions_to_find)
            if files:
                return files

    return find_files_with_extensions(clone_dir, extensions_to_find)

def find_files_with_extensions(root_dir, extensions):
    """Recursively search for artifacts in common output folders (libs, outputs, target, etc.)."""
    valid_artifact_dirs = ['libs', 'outputs', 'target', 'build']
    found_files = []

    for dirpath, _, filenames in os.walk(root_dir):
        # Exclude gradle cache, wrappers, and git internals
        if any(ign in dirpath for ign in ['.gradle', '.git', 'gradle-wrapper', 'wrapper']):
            continue
        if any(valid_dir in dirpath.replace(os.sep, '/') for valid_dir in valid_artifact_dirs):
            for file in filenames:
                if any(file.endswith(ext) for ext in extensions):
                    full_path = os.path.join(dirpath, file)
                    # Exclude gradle test worker jars
                    if "test-worker" not in file and "testRunner" not in file:
                        found_files.append(full_path)

    # Sort so that .aar and release jars come before debug/test jars
    def artifact_rank(f):
        name = os.path.basename(f).lower()
        if name.endswith('.aar'):
            return 0
        if 'release' in name:
            return 1
        if not any(k in name for k in ['test', 'debug', 'sources', 'javadoc']):
            return 2
        return 3

    found_files.sort(key=artifact_rank)
    return found_files

def save_artifact(artifact_files, organization, module, version, dest_dir=None):
    """
    Copies built artifact files to the repository destination directory and generates checksums.
    Uses shutil.copy2 to support cross-drive and cross-volume paths.
    """
    if dest_dir is None:
        dest_dir = getArtifactDest(organization, module, version)
    os.makedirs(dest_dir, exist_ok=True)

    primary_file = None
    for artifact in artifact_files:
        ending = getEnding(artifact)
        base_name = os.path.basename(artifact)

        # Check for classifiers (e.g. -sources, -javadoc)
        classifier = ""
        if "-sources" in base_name:
            classifier = "-sources"
        elif "-javadoc" in base_name:
            classifier = "-javadoc"

        dest_file = os.path.join(dest_dir, f"{module}-{version}{classifier}{ending}")
        print(f"Saving artifact: {artifact} -> {dest_file}")
        shutil.copy2(artifact, dest_file)

        # Generate SHA1 and MD5
        write_file_checksums(dest_file)

        if not classifier and primary_file is None:
            primary_file = dest_file

    return primary_file or (dest_file if artifact_files else None)

def write_file_checksums(file_path):
    """Computes and writes SHA1 and MD5 checksum files."""
    try:
        sha1 = hashlib.sha1()
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha1.update(chunk)
                md5.update(chunk)
        with open(f"{file_path}.sha1", 'w', encoding='utf-8') as f:
            f.write(sha1.hexdigest() + '\n')
        with open(f"{file_path}.md5", 'w', encoding='utf-8') as f:
            f.write(md5.hexdigest() + '\n')
    except Exception as e:
        print(f"Error computing checksums for {file_path}: {e}")

def getPackagings(artifact_files):
    """Returns primary packaging extension (e.g. 'aar' or 'jar')."""
    if not artifact_files:
        return 'jar'
    first = artifact_files[0]
    return getEnding(first).replace(".", "").lower()

def getArtifactDest(organization, repo, version):
    group_path = organization.replace('.', os.sep).replace('/', os.sep)
    dest_dir = os.path.join(LOCAL_REPO_PATH, group_path, repo, version)
    return dest_dir

def getEnding(artifact):
    return os.path.splitext(artifact)[-1]

def remove_line_with_partial_match(file_path, match_string):
    replace_line_with_partial_match(file_path, match_string, "")

def replace_line_with_partial_match(file_path, match_string, replacement_string):
    if not os.path.exists(file_path):
        return
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
        new_lines = [replacement_string + ('\n' if replacement_string and not replacement_string.endswith('\n') else '')
                     if match_string in line else line for line in lines]
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(new_lines)
    except Exception as e:
        print(f"Error replacing partial match in {file_path}: {e}")

def replace_in_file(file_path, old_line, new_line):
    if not os.path.exists(file_path):
        return
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read().replace(old_line, new_line)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
    except Exception as e:
        print(f"Error replacing in {file_path}: {e}")

