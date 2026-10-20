import os
import sys
import subprocess
from glob import glob
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH
import xml.etree.ElementTree as ET
import re
from build_utils.build_utils import *


import os
import sys
import subprocess
import re
from build_utils.build_utils import (
    remove_line_with_partial_match,
    replace_line_with_partial_match,
    replace_in_file
)

class GradleUtils:

    # https://docs.gradle.org/current/userguide/compatibility.html#java_runtime
    GRADLE_JAVA_VERSIONS = {
        (3, 0): ['7', '8'],
        (4, 0): ['7', '8'],
        (4, 3): ['7', '8', '9'],
        (4, 7): ['7', '8', '9', '10'],
        (5, 0): ['8', '11'],
        (5, 4): ['8', '11', '12'],
        (6, 0): ['8', '11', '12', '13'],
        (6, 3): ['8', '11', '12', '13', '14'],
        (6, 7): ['8', '11', '12', '13', '14', '15'],
        (7, 0): ['11', '12', '13', '14', '15', '16'],
        (7, 3): ['11', '12', '13', '14', '15', '16', '17'],
        (7, 5): ['11', '12', '13', '14', '15', '16', '17', '18'],
        (7, 6): ['11', '12', '13', '14', '15', '16', '17', '18', '19'],
        (8, 0): ['11', '12', '13', '14', '15', '16', '17', '18', '19'],
        (8, 3): ['11', '12', '13', '14', '15', '16', '17', '18', '19', '20'],
        (8, 5): ['11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21'],
        (8, 10): ['17', '21'],
    }

    LATEST_GRADLE_JAVA_VERSIONS = ['17', '21']

    def update_build_files(self, clone_dir):
        suffixes = ["", ".kts"]
        for suffix in suffixes:
            self.replace_jitpack(clone_dir, suffix)
            self.remove_Jcenter(clone_dir, suffix)
            self.replace_custom(clone_dir, suffix)
            self.set_compile_version(clone_dir, suffix)

    def replace_custom(self, clone_dir, suffix):
        publish_gradle = os.path.join(clone_dir, 'publish.gradle' + suffix)
        if os.path.exists(publish_gradle):
            remove_line_with_partial_match(publish_gradle, "com.novoda:bintray-release")

        build_gradle = os.path.join(clone_dir, 'build.gradle' + suffix)
        if os.path.exists(build_gradle):
            remove_line_with_partial_match(build_gradle, "apply from: 'https://raw.githubusercontent.com/")

    def replace_jitpack(self, clone_dir, suffix):
        old_line = '"https://jitpack.io"'
        new_line = '"http://127.0.0.1:5000/repository"'
        replace_in_file(os.path.join(clone_dir, 'build.gradle' + suffix), old_line, new_line)
        replace_in_file(os.path.join(clone_dir, 'settings.gradle' + suffix), old_line, new_line)

    def remove_Jcenter(self, clone_dir, suffix):
        build_gradle = os.path.join(clone_dir, 'build.gradle' + suffix)
        settings_gradle = os.path.join(clone_dir, 'settings.gradle' + suffix)
        wrapper_gradle = os.path.join(clone_dir, 'gradle', 'wrapper', 'gradle-wrapper.properties')

        # Remove dead bintray / jcenter plugins
        remove_line_with_partial_match(build_gradle, "com.novoda:bintray-release")
        remove_line_with_partial_match(build_gradle, "com.jfrog.bintray.gradle:gradle-bintray-plugin")

        # Upgrade ancient Android Gradle plugin 2.x -> 3.0.0
        old_line = 'com.android.tools.build:gradle:2'
        new_line = "classpath 'com.android.tools.build:gradle:3.0.0'"
        replace_line_with_partial_match(build_gradle, old_line, new_line)
        replace_line_with_partial_match(settings_gradle, old_line, new_line)

        # Elevate ancient Gradle wrappers 1.x, 2.x, 3.x to Gradle 4.1
        if os.path.exists(wrapper_gradle):
            new_line = "distributionUrl=https\\://services.gradle.org/distributions/gradle-4.1-all.zip"
            replace_line_with_partial_match(wrapper_gradle, 'distributionUrl=https\\://services.gradle.org/distributions/gradle-3.', new_line)
            replace_line_with_partial_match(wrapper_gradle, 'distributionUrl=https\\://services.gradle.org/distributions/gradle-2.', new_line)
            replace_line_with_partial_match(wrapper_gradle, 'distributionUrl=https\\://services.gradle.org/distributions/gradle-1.', new_line)
            replace_line_with_partial_match(wrapper_gradle, 'distributionUrl=http\\://services.gradle.org/distributions/gradle-3.', new_line)
            replace_line_with_partial_match(wrapper_gradle, 'distributionUrl=http\\://services.gradle.org/distributions/gradle-2.', new_line)
            replace_line_with_partial_match(wrapper_gradle, 'distributionUrl=http\\://services.gradle.org/distributions/gradle-1.', new_line)

        # Replace jcenter() repository with mavenCentral() and Google
        replacement_repos = """
            mavenCentral()
            maven {
                url 'https://maven.google.com/'
                name 'Google'
            }
        """
        replace_line_with_partial_match(build_gradle, 'jcenter()', replacement_repos)
        replace_line_with_partial_match(settings_gradle, 'jcenter()', replacement_repos)

    def get_gradlew_path(self, clone_dir):
        if os.name == 'nt':
            gradlew = os.path.join(clone_dir, "gradlew.bat")
        else:
            gradlew = os.path.join(clone_dir, "gradlew")
            if os.path.exists(gradlew):
                try:
                    os.chmod(gradlew, 0o755)
                except Exception as e:
                    print(f"Could not chmod gradlew: {e}")
        return gradlew

    def build_project(self, clone_dir, target_module=None):
        gradlew = self.get_gradlew_path(clone_dir)
        if not os.path.exists(gradlew):
            # Fallback to system gradle if gradlew is missing
            gradlew = "gradle"

        # If a specific module was requested (Issue #1: Multi-Module Builds)
        if target_module:
            clean_module = target_module.strip(":")
            # Try module-specific assembleRelease or build
            tasks_to_try = [
                [f":{clean_module}:assembleRelease"],
                [f":{clean_module}:build"],
                ["assembleRelease"],
                ["build"]
            ]
            for task in tasks_to_try:
                code = self.run_gradle_task(gradlew, clone_dir, task)
                if code == 0:
                    print(f"Module build succeeded with task {task}")
                    return

        # General build: find modules or run assembleRelease / build
        modules = self.find_gradle_modules(clone_dir)
        exit_codes = []
        if modules:
            for mod in modules:
                mod_path = os.path.join(clone_dir, mod.replace(":", os.sep))
                self.update_build_files(mod_path)
                code = self.build_module(clone_dir, mod, gradlew)
                exit_codes.append(code)

        if not modules or all(c != 0 for c in exit_codes):
            # Try root build
            print("Trying root assembleRelease or build")
            code = self.run_gradle_task(gradlew, clone_dir, ["assembleRelease"])
            if code != 0:
                code = self.run_gradle_task(gradlew, clone_dir, ["build", "-x", "test"])
            exit_codes.append(code)

        if all(code != 0 for code in exit_codes):
            raise Exception(f"No Gradle build succeeded. Exit codes: {exit_codes}")

    def build_module(self, clone_dir, module, gradlew=None):
        if gradlew is None:
            gradlew = self.get_gradlew_path(clone_dir)
            if not os.path.exists(gradlew):
                gradlew = "gradle"

        commands = []
        if module:
            clean_module = module.strip(":")
            commands = [[f':{clean_module}:assembleRelease'], [f':{clean_module}:build']]
        else:
            commands = [["assembleRelease"], ["build", "-x", "test"]]

        for cmd in commands:
            exit_code = self.run_gradle_task(gradlew, clone_dir, cmd)
            if exit_code == 0:
                return 0

        return 1

    def run_gradle_task(self, gradlew, cwd, tasks):
        print(f"Running gradle task: {gradlew} {' '.join(tasks)} in {cwd}")
        try:
            output = subprocess.run(
                [gradlew, *tasks],
                cwd=cwd,
                capture_output=True
            )
            stdout_str = output.stdout.decode('utf-8', errors='replace')
            stderr_str = output.stderr.decode('utf-8', errors='replace')
            sys.stdout.write(stdout_str)
            sys.stderr.write(stderr_str)

            if output.returncode != 0:
                print(f"Task {tasks} failed with return code {output.returncode}")
            return output.returncode
        except Exception as e:
            print(f"Failed to execute {gradlew}: {e}")
            return 1

    def find_gradle_modules(self, root_dir):
        """Find Gradle modules by searching for build.gradle files."""
        modules = []
        for root, dirs, files in os.walk(root_dir):
            if any(f in files for f in ['build.gradle', 'build.gradle.kts']):
                rel = os.path.relpath(root, root_dir)
                if rel != ".":
                    module_name = rel.replace(os.sep, ":")
                    modules.append(module_name)
        return modules

    def extract_gradle_version(self, folder):
        """Extract the Gradle version from gradle-wrapper.properties."""
        wrapper_properties_file = os.path.join(folder, 'gradle', 'wrapper', 'gradle-wrapper.properties')
        if os.path.exists(wrapper_properties_file):
            try:
                with open(wrapper_properties_file, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                match = re.search(r'gradle-(\d+\.\d+)', content)
                if match:
                    return match.group(1)
            except Exception as e:
                print(f"Error reading gradle wrapper properties: {e}")
        return None

    def get_java_versions_from_gradle(self, gradle_version):
        """Get the possible Java versions supported by the Gradle version with fallback."""
        try:
            major, minor = map(int, gradle_version.split('.')[:2])
        except ValueError:
            return self.LATEST_GRADLE_JAVA_VERSIONS

        java_versions = self.GRADLE_JAVA_VERSIONS.get((major, minor), [])
        if not java_versions:
            available_versions = sorted(self.GRADLE_JAVA_VERSIONS.keys())
            for (v_major, v_minor) in reversed(available_versions):
                if v_major < major or (v_major == major and v_minor <= minor):
                    java_versions = self.GRADLE_JAVA_VERSIONS[(v_major, v_minor)]
                    break

        return java_versions or self.LATEST_GRADLE_JAVA_VERSIONS

    def determine_java_version(self, folder):
        gradle_version = self.extract_gradle_version(folder)
        if gradle_version:
            versions = self.get_java_versions_from_gradle(gradle_version)
            print(f"Gradle version detected: {gradle_version}, compatible Java versions: {versions}")
            return versions
        else:
            return self.LATEST_GRADLE_JAVA_VERSIONS

    def get_agp_version(self, root_dir, suffix):
        build_file = os.path.join(root_dir, "build.gradle" + suffix)
        if os.path.exists(build_file):
            try:
                with open(build_file, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                agp_version_match = re.search(r'com.android.tools.build:gradle:(\d+\.\d+)', content)
                if agp_version_match:
                    return agp_version_match.group(1)
            except Exception as e:
                print(f"Error reading {build_file}: {e}")
        return None

    def update_gradle_file(self, file_path, use_new_syntax):
        if not os.path.exists(file_path):
            return
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()

            modified = False
            new_lines = []
            for line in lines:
                new_line = line
                if use_new_syntax:
                    if 'compileSdkVersion' in line:
                        new_line = line.replace('compileSdkVersion', 'compileSdk')
                        modified = True
                    elif 'targetSdkVersion' in line:
                        new_line = line.replace('targetSdkVersion', 'targetSdk')
                        modified = True
                    elif 'minSdkVersion' in line:
                        new_line = line.replace('minSdkVersion', 'minSdk')
                        modified = True
                new_lines.append(new_line)

            if modified:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(new_lines)
        except Exception as e:
            print(f"Error updating {file_path}: {e}")

    def find_and_update_gradle_files(self, root_dir, use_new_syntax):
        for root, dirs, files in os.walk(root_dir):
            for file_name in ['build.gradle', 'build.gradle.kts']:
                if file_name in files:
                    self.update_gradle_file(os.path.join(root, file_name), use_new_syntax)

    def set_compile_version(self, root_dir, suffix):
        agp_version = self.get_agp_version(root_dir, suffix)
        if agp_version:
            try:
                agp_major = float(agp_version)
                use_new_syntax = agp_major >= 7.0
                self.find_and_update_gradle_files(root_dir, use_new_syntax)
            except ValueError:
                pass