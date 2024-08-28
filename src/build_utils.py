import os
import sys
import subprocess
from glob import glob
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH

def update_build_files(clone_dir):
    replace_jitpack(clone_dir)
    remove_Jcenter(clone_dir)

def replace_jitpack(clone_dir):
    # Replace jitpack when used. May be useful if jitpack is down.
    old_line = '"https://jitpack.io"'
    new_line = '"http://127.0.0.1:5000/repository"'
    replace_in_file(os.path.join(clone_dir, 'build.gradle'), old_line, new_line)
    replace_in_file(os.path.join(clone_dir, 'settings.gradle'), old_line, new_line)

def remove_Jcenter(clone_dir):
    build_gradle = os.path.join(clone_dir, 'build.gradle')
    settings_gradle = os.path.join(clone_dir, 'settings.gradle')
    wrapper_gradle = os.path.join(clone_dir, 'gradle', 'wrapper', 'gradle-wrapper.properties')
    
    remove_line_with_partial_match(build_gradle, "com.novoda:bintray-release")
    remove_line_with_partial_match(build_gradle, "com.jfrog.bintray.gradle:gradle-bintray-plugin")

    # Bump gradle tools versions.
    old_line = 'com.android.tools.build:gradle:2'
    new_line = "classpath 'com.android.tools.build:gradle:3.0.0'"
    replace_line_with_partial_match(build_gradle, old_line, new_line)
    replace_line_with_partial_match(settings_gradle, old_line, new_line)
    
    # Bump gradle wrapper versions.
    new_line = "distributionUrl=https\://services.gradle.org/distributions/gradle-4.1-all.zip'"
    old_line = 'distributionUrl=https\://services.gradle.org/distributions/gradle-3.'
    replace_line_with_partial_match(wrapper_gradle, old_line, new_line)
    old_line = 'distributionUrl=https\://services.gradle.org/distributions/gradle-2.'
    replace_line_with_partial_match(wrapper_gradle, old_line, new_line)
    old_line = 'distributionUrl=https\://services.gradle.org/distributions/gradle-1.'
    replace_line_with_partial_match(wrapper_gradle, old_line, new_line)

    # replace jcenter only repos with other repos.
    old_line = 'jcenter()'
    new_line = """
        mavenCentral()
        maven {
            url 'https://maven.google.com/'
            name 'Google'
        }
        """
    replace_line_with_partial_match(build_gradle, old_line, new_line)
    replace_line_with_partial_match(settings_gradle, old_line, new_line)
    
    # replace google() as it is not found sometimes.
    old_line = 'google()'
    new_line = """
        mavenCentral()
        maven {
            url 'https://maven.google.com/'
            name 'Google'
        }
        """
    replace_line_with_partial_match(build_gradle, old_line, new_line)
    replace_line_with_partial_match(settings_gradle, old_line, new_line)
    
def remove_line_with_partial_match(file_path, match_string):
    replace_line_with_partial_match(file_path, match_string, "")

def replace_line_with_partial_match(file_path, match_string, replacement_string):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    new_lines = [replacement_string if match_string in line else line for line in lines]
    with open(file_path, 'w') as file:
        file.writelines(new_lines)

def replace_in_file(file_path, old_line, new_line):
    with open(file_path, 'r') as file:
        content = file.read().replace(old_line, new_line)
    with open(file_path, 'w') as file:
        file.write(content)

def build_project(clone_dir):
    command =  "assembleRelease" # Maybe leading to problems with LeakCanary
    command =  "assemble"
    subprocess.run(["gradlew.bat", command], cwd=clone_dir, check=True, shell=True)
    # TODO: Leading to error as we have mocked them to pipe them into a file.
    # , stdin=sys.stdout, stderr=sys.stderr

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