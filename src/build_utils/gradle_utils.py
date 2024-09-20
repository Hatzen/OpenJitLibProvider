import os
import sys
import subprocess
from glob import glob
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH
import xml.etree.ElementTree as ET
import re
from build_utils.build_utils import *


class GradleUtils():

    def update_build_files(self, clone_dir):
        suffixs = ["", ".kts"]
        for suffix in suffixs:
            self.replace_jitpack(clone_dir, suffix)
            self.remove_Jcenter(clone_dir, suffix)
            self.replace_custom(clone_dir, suffix)
            self.set_compile_version(clone_dir, suffix)

    def replace_custom(self, clone_dir, suffix):
        # needed for skydoves:elasticviews
        publish_gradle = os.path.join(clone_dir, 'publish.gradle' + suffix)
        try:
            remove_line_with_partial_match(publish_gradle, "com.novoda:bintray-release") # TODO: Remove in all files as gradle could be split up
        except:
            pass # publish file not existing

        build_gradle = os.path.join(clone_dir, 'build.gradle' + suffix)
        # needed for pvasa:EasyCrypt
        remove_line_with_partial_match(build_gradle, "apply from: 'https://raw.githubusercontent.com/")

    def replace_jitpack(self, clone_dir, suffix):
        # Replace jitpack when used. May be useful if jitpack is down.
        old_line = '"https://jitpack.io"'
        new_line = '"http://127.0.0.1:5000/repository"'
        replace_in_file(os.path.join(clone_dir, 'build.gradle' + suffix), old_line, new_line)
        replace_in_file(os.path.join(clone_dir, 'settings.gradle'+ suffix), old_line, new_line)

    def remove_Jcenter(self, clone_dir, suffix):
        build_gradle = os.path.join(clone_dir, 'build.gradle' + suffix)
        settings_gradle = os.path.join(clone_dir, 'settings.gradle' + suffix)
        wrapper_gradle = os.path.join(clone_dir, 'gradle', 'wrapper', 'gradle-wrapper.properties')
        
        remove_line_with_partial_match(build_gradle, "com.novoda:bintray-release")
        remove_line_with_partial_match(build_gradle, "com.jfrog.bintray.gradle:gradle-bintray-plugin")

        # Bump gradle tools versions.
        old_line = 'com.android.tools.build:gradle:2'
        new_line = "classpath 'com.android.tools.build:gradle:3.0.0'"
        replace_line_with_partial_match(build_gradle, old_line, new_line)
        replace_line_with_partial_match(settings_gradle, old_line, new_line)
        
        # Bump gradle wrapper versions. As tools need to be compatible and old versions only existed in jcenter.
        new_line = "distributionUrl=https\://services.gradle.org/distributions/gradle-4.1-all.zip"
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
        
    def build_project(self, clone_dir):

        modules = self.find_gradle_modules(clone_dir)

        exitCodes = []
        for module in modules:
            modulepath = os.path.join(clone_dir, module)
            self.update_build_files(modulepath)
            exitCode = self.build_module(clone_dir, module)
            exitCodes.append(exitCode)

        noArtifcat = all(exitCode != 0 for exitCode in exitCodes)
        if noArtifcat:
            raise Exception("No build succeeded " + str(exitCodes))
            # When failing with
            # > com.android.ide.common.signing.KeytoolException: Failed to read key AndroidDebugKey from store "C:\Users\xxx\.android\debug.keystore": Integrity check failed: java.security.NoSuchAlgorithmException: Algorithm HmacPBESHA256 not available
            # then jdk 12 and above is needed


    def build_module(self, clone_dir, module):

        command = [f':{module}:build'] if module else ['build']
        # command = ["assemble"]
        # command = ["assembleRelease"]
        # command = ["build"]

        print("build module" + module)
        
        if os.name == 'nt':
            replaced = clone_dir.replace("/",  "\\")
            gradlew = os.path.join(os.getcwd(), replaced, "gradlew.bat")
            gradlew = gradlew.replace("/",  "\\")
        else:
            gradlew = os.path.join(os.getcwd(), replaced, "gradlew")


        # Avoid signing apks, may lead to problems with hash not available (might be resolved by using newest java version.)
        assemble_release_tasks = self.find_assemble_release_tasks(gradlew, clone_dir, 'signReleaseBundle')
        #if assemble_release_tasks:
        #    # command += '  -x signReleaseBundle '
        #    command += ['-x', 'signReleaseBundle']
        
        print("using gradlewrapper: " + gradlew)
        output = subprocess.run([gradlew, *command], cwd=clone_dir,capture_output=True)
        
        # print("output")
        # print(output)
        sys.stdout.write(output.stdout.decode())
        sys.stderr.write(output.stderr.decode())

        exitCode = output.returncode
        if exitCode != 0:
            print("failed {module} build with returncode " + str(exitCode))
        return exitCode

    def find_gradle_modules(self, root_dir):
        """
        Find all Gradle modules that build APKs by searching for 'com.android.application' in build files.
        """
        apk_modules = []
        for root, dirs, files in os.walk(root_dir):
            for file_name in ['build.gradle', 'build.gradle.kts']:
                if file_name in files:
                    build_file_path = os.path.join(root, file_name)
                    # Check if the module builds an APK
                    if not self.is_apk_build_module(build_file_path):
                        # Get relative path of the module
                        module_path = os.path.relpath(root, root_dir).replace(os.sep, ":")
                        if module_path == ".":
                            module_path = ""
                        apk_modules.append(module_path)
        return apk_modules


    def is_apk_build_module(self, build_file_path):
        """
        Check if the module builds an APK by inspecting the build.gradle or build.gradle.kts file.
        """
        try:
            with open(build_file_path, 'r') as file:
                content = file.read()
                # Check if the module applies the 'com.android.application' plugin
                if 'com.android.application' in content:
                    return True
        except Exception as e:
            print(f"Error reading {build_file_path}: {e}")
        return False

    # https://docs.gradle.org/current/userguide/compatibility.html#java_runtime
    GRADLE_JAVA_VERSIONS = {
        (3, 0): ['7', '8'], # theoretically not needed as should be bumbed to version 4
        (4, 0): ['7', '8'],
        (5, 0): ['8', '11'],
        (5, 4): ['8', '11', '12'],
        (6, 0): ['8', '11', '12', '13'],
        (6, 3): ['8', '11', '12', '13', '14'],
        (6, 7): ['8', '11', '12', '13', '14', '15'],
        (7, 0): ['11', '12', '13', '14', '15', '16'],
        (7, 3): ['11', '12', '13', '14', '15', '16', '17'],
        (7, 5): ['11', '12', '13', '14', '15', '16', '17', '18'],
        (7, 6): ['11', '12', '13', '14', '15', '16', '17', '18', '19'],
        (8, 3): ['11', '12', '13', '14', '15', '16', '17', '18', '19', '20'],
        (8, 5): ['11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21'],
    }

    LATEST_GRADLE_JAVA_VERSIONS = ['17', '21']

    def detect_project_type(self, folder):
        """Detect if the folder is a Maven or Gradle project based on the presence of key files."""
        if os.path.exists(os.path.join(folder, 'pom.xml')):
            return 'maven'
        elif os.path.exists(os.path.join(folder, 'build.gradle')) or os.path.exists(os.path.join(folder, 'settings.gradle')):
            return 'gradle'
        else:
            return 'unknown'

    def extract_gradle_version(self, folder):
        """Extract the Gradle version from gradle-wrapper.properties."""
        wrapper_properties_file = os.path.join(folder, 'gradle', 'wrapper', 'gradle-wrapper.properties')
        if os.path.exists(wrapper_properties_file):
            with open(wrapper_properties_file, 'r') as file:
                content = file.read()
            match = re.search(r'gradle-(\d+\.\d+)', content)
            #print("trial version match: " + str(match))
            #print("in content " + str(content))
            if match:
                return match.group(1)
        print("gradle properties not found " + wrapper_properties_file)
        return None

    def get_java_versions_from_gradle(self, gradle_version):
        """Get the possible Java versions supported by the Gradle version with fallback to latest version."""

        print("Looking for java version for gradle wrapper version" + gradle_version)

        # Extrahiere die Haupt- und Nebenversion aus der Gradle-Version
        try:
            major, minor = map(int, gradle_version.split('.')[:2])
        except ValueError:
            return []

        # find exact match
        java_versions = self.GRADLE_JAVA_VERSIONS.get((major, minor), [])

        # if no direct match find next higher Minor-Version
        if not java_versions:
            # look for highest version that is lower equal than the needed version
            available_versions = sorted(self.GRADLE_JAVA_VERSIONS.keys())
            for (v_major, v_minor) in reversed(available_versions):
                if v_major < major or (v_major == major and v_minor <= minor):
                    java_versions = self.GRADLE_JAVA_VERSIONS[(v_major, v_minor)]
                    break
        if not java_versions:
            java_versions = self.GRADLE_JAVA_VERSIONS[(v_major, v_minor)]
        return java_versions

    def determine_java_version(self, folder):
        gradle_version = self.extract_gradle_version(folder)
        if gradle_version:
            versions = self.get_java_versions_from_gradle(gradle_version)
            print(f"Gradle version detected: {gradle_version}")
            print(f"Possible Java versions: {versions}")
            return versions
        else:
            print("Gradle - No Gradle wrapper version found.")
            return self.GRADLE_JAVA_VERSIONS[-1] # use latest version
        

    def get_gradle_tasks(self, gradlew, cwd):
        try:
            result = subprocess.run([gradlew, "tasks", "--all"], cwd=cwd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Fehler beim Ausführen von gradlew tasks: {e}")
            print(f"Fehlerausgabe (stderr): {e.stderr}")
            print(f"Standardausgabe (stdout): {e.stdout}")
            return None

    def find_assemble_release_tasks(self, gradlew, cwd,  taskToFind):

        output = self.get_gradle_tasks(gradlew, cwd)
        if not output:
            raise Exception("cannot get task list")
            
        #print("assemble_tasks")
        #print(assemble_tasks)
        if taskToFind not in output:
            print("no findings in task list output for " + taskToFind)
            print("available tasks:")
            print(output)
            return False
        
        
        return True
    





    def get_agp_version(self, root_dir, suffix):
        """
        Extract the Android Gradle Plugin (AGP) version from the root build.gradle file.
        """
        build_file = os.path.join(root_dir, "build.gradle" + suffix)
        try:
            with open(build_file, 'r') as file:
                content = file.read()
                # Regex to find AGP version in classpath
                agp_version_match = re.search(r'com.android.tools.build:gradle:(\d+\.\d+)', content)
                if agp_version_match:
                    agp_version = agp_version_match.group(1)
                    print(f"Detected AGP version: {agp_version}")
                    return agp_version
        except Exception as e:
            print(f"Error reading {build_file}: {e}")
        return None

    def update_gradle_file(self, file_path, use_new_syntax):
        """
        Update a Gradle build file by changing between old and new syntax based on use_new_syntax flag.
        """
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()

            modified = False
            new_lines = []
            for line in lines:
                new_line = line
                if use_new_syntax:
                    # Change old -> new
                    if 'compileSdkVersion' in line:
                        new_line = line.replace('compileSdkVersion', 'compileSdk')
                        modified = True
                    elif 'targetSdkVersion' in line:
                        new_line = line.replace('targetSdkVersion', 'targetSdk')
                        modified = True
                    elif 'minSdkVersion' in line:
                        new_line = line.replace('minSdkVersion', 'minSdk')
                        modified = True
                else:
                    # Change new -> old
                    if 'compileSdk' in line and 'compileSdkVersion' not in line :
                        new_line = line.replace('compileSdk', 'compileSdkVersion')
                        modified = True
                    elif 'targetSdk' in line and 'targetSdkVersion' not in line :
                        new_line = line.replace('targetSdk', 'targetSdkVersion')
                        modified = True
                    elif 'minSdk' in line and 'minSdkVersion' not in line :
                        new_line = line.replace('minSdk', 'minSdkVersion')
                        modified = True
                
                new_lines.append(new_line)

            # If changes were made, rewrite the file
            if modified:
                with open(file_path, 'w') as file:
                    file.writelines(new_lines)
                print(f"Updated {file_path}")
            else:
                print(f"No changes needed in {file_path}")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    def find_and_update_gradle_files(self, root_dir, use_new_syntax):
        """
        Recursively find all 'build.gradle' and 'build.gradle.kts' files in the project and update them.
        """
        for root, dirs, files in os.walk(root_dir):
            for file_name in ['build.gradle', 'build.gradle.kts']:
                if file_name in files:
                    gradle_file_path = os.path.join(root, file_name)
                    self.update_gradle_file(gradle_file_path, use_new_syntax)

    def set_compile_version(self, root_dir, suffix):

        # Detect the AGP version
        agp_version = self.get_agp_version(root_dir, suffix)

        # Determine whether to use new or old syntax
        if agp_version:
            agp_major_version = float(agp_version)
            if agp_major_version >= 7.0:
                print("Using new Gradle syntax (AGP 7.0+)")
                use_new_syntax = True
            else:
                print("Using old Gradle syntax (AGP < 7.0)")
                use_new_syntax = False

            # Use new syntax as we use very new android sdk
            # use_new_syntax = False

            # Find and update all Gradle build files
            self.find_and_update_gradle_files(root_dir, use_new_syntax)
        else:
            print("Could not determine AGP version. No changes made.")

    