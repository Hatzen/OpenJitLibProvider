import os
import subprocess
from glob import glob
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH

def update_build_files(clone_dir):
    old_line = '"https://jitpack.io"'
    new_line = '"http://127.0.0.1:5000/repository"'
    replace_line_in_file(os.path.join(clone_dir, 'build.gradle'), old_line, new_line)
    replace_line_in_file(os.path.join(clone_dir, 'settings.gradle'), old_line, new_line)
    
'''
update version 2 to 3
        classpath 'com.android.tools.build:gradle:3.0.0'


replace jcenter only; with  2x

    repositories {
        mavenCentral()
        // google() not found 
        
        maven {
            url 'https://maven.google.com/'
            name 'Google'
        }
        jcenter()
    }

update wrapper to 4.1

'''


def replace_line_in_file(file_path, old_line, new_line):
    with open(file_path, 'r') as file:
        content = file.read().replace(old_line, new_line)
    with open(file_path, 'w') as file:
        file.write(content)

def build_project(clone_dir):
    subprocess.run(["gradlew.bat", "assembleRelease"], cwd=clone_dir, check=True, shell=True)

def find_artifact_file(clone_dir):
    for filename in glob(os.path.join(clone_dir, '**', '*.aar'), recursive=True):
        print(f"Found AAR file: {filename}")
        return filename
    return None

def save_artifact(jar_file, organization, module, version):
    dest_dir = getArtifactDest(organization, module, version)
    dest_file = os.path.join(dest_dir, f"{module}-{version}.aar")
    os.makedirs(dest_dir, exist_ok=True)
    os.rename(jar_file, dest_file)
    return dest_file

def getArtifactDest(organization, module, version):
    group_path = organization.replace('.', '/')
    dest_dir = os.path.join(LOCAL_REPO_PATH, group_path, module, version)
    return dest_dir