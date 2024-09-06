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
        self.replace_jitpack(clone_dir)
        self.remove_Jcenter(clone_dir)

    def replace_jitpack(self, clone_dir):
        # Replace jitpack when used. May be useful if jitpack is down.
        old_line = '"https://jitpack.io"'
        new_line = '"http://127.0.0.1:5000/repository"'
        replace_in_file(os.path.join(clone_dir, 'build.gradle'), old_line, new_line)
        replace_in_file(os.path.join(clone_dir, 'settings.gradle'), old_line, new_line)

    def remove_Jcenter(self, clone_dir):
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
        
    def build_project(self, clone_dir):
        command =  "clean assembleRelease" # Maybe leading to problems with LeakCanary
        command = "assemble" # Problems with sign https://stackoverflow.com/questions/67631927/error-building-aab-flutter-android-integrity-check-failed-java-security-n
        command = "assemble -x signRelease" # gibts nicht
        command = "assembleDebug"

        
        print("build project in")
        # process = subprocess.run(["./gradlew.bat", command], cwd=clone_dir,stdout=subprocess.PIPE,stderr=subprocess.PIPE, check=True, shell=True)
        
        
        replaced = clone_dir.replace("/",  "\\")
        
        # printJavaVersion(os.path.join(os.getcwd(), replaced))
        
        gradlew = os.path.join(os.getcwd(), replaced, "gradlew.bat")
        gradlew = gradlew.replace("/",  "\\")
        
        print(gradlew)
        # process = subprocess.run([gradlew, command], cwd=os.path.join(os.getcwd(), clone_dir),stdout=subprocess.PIPE,stderr=subprocess.PIPE, check=True, shell=True)
        # process = subprocess.run([gradlew,  "assemble", "-x", "signRelease" ], cwd=clone_dir, check=True)
        process = subprocess.run([gradlew, command], cwd=clone_dir, check=True)
        
        
        # process = subprocess.run([gradlew, command], cwd=os.path.join(os.getcwd(), clone_dir),stdout=subprocess.PIPE,stderr=subprocess.PIPE, check=True, shell=True)
        # process = subprocess.run(["gradlew.bat", command], cwd=clone_dir, check=True)
        
        # process = subprocess.run(["./gradlew.bat", command], cwd=clone_dir, capture_output=True)    
        # process = subprocess.run(["gradlew.bat", command], cwd=clone_dir, capture_output=True)


        # TODO: Leading to error as we have mocked them to pipe them into a file.
        # , stdin=sys.stdout, stderr=sys.stderr
        
        # Needed when sys.stdout is catched.
        # tdout, stderr = process.communicate()
        # tdout.seek(0)
        # tderr.seek(0)
        # ys.stdout.write(stdout.decode())
        # ys.stderr.write(stderr.decode())


    ALL_JAVA_VERSION_DESC = ['21', '17','11','8' ]

    # https://docs.gradle.org/current/userguide/compatibility.html#java_runtime
    GRADLE_JAVA_VERSIONS = {
        (4, 0): ['7', '8'],
        (5, 0): ['8', '11'],
        (6, 0): ['8', '11', '12', '13', '14', '15'],
        (6, 5): ['8', '11', '12', '13', '14', '15'],
        (6, 8): ['8', '11', '12', '13', '14', '15'],
        (7, 0): ['11', '12', '13', '14', '15', '16'],
        (7, 3): ['11', '17'],
        (7, 6): ['11', '17'],
        (7, 9): ['11', '17'],
        (8, 0): ['11', '17', '21'],
        (8, 1): ['11', '17', '21'],
        (8, 2): ['11', '17', '21'],
        (8, 3): ['11', '17', '21'],
        (8, 4): ['11', '17', '21'],
        (8, 5): ['11', '17', '21'],
    }

    # Fallback-Werte für die neueste bekannte Version
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
            # match = re.search(r'distributionUrl=https://services.gradle.org/distributions/gradle-(\d+\.\d+)\.zip', content)
            # match = re.search(r'distributionUrl=https://services.gradle.org/distributions/gradle-(\d+\.\d+)(?:\.\d+)?-\w+\.zip', content)
            # match = re.search(r'distributionUrl=https://services.gradle.org/distributions/gradle-(\d+\.\d+)*.zip', content)
            # match = re.search(r'*gradle-(\d+\.\d+)*', content)
            match = re.search(r'gradle-(\d+\.\d+)', content)
            print("trial version match: " + str(match))
            print("in content " + str(content))
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

        # Versuche, die Java-Versionen für die genaue Version zu finden
        java_versions = self.GRADLE_JAVA_VERSIONS.get((major, minor), [])

        # Wenn keine Version gefunden wurde, suche nach der nächsthöheren Minor-Version
        if not java_versions:
            # Suche nach der höchsten unterstützten Version, die kleiner oder gleich der angegebenen Version ist
            available_versions = sorted(self.GRADLE_JAVA_VERSIONS.keys())
            for (v_major, v_minor) in reversed(available_versions):
                if v_major < major or (v_major == major and v_minor <= minor):
                    java_versions = self.GRADLE_JAVA_VERSIONS[(v_major, v_minor)]
                    break
        return java_versions
        
        # TODO: Remove
        #versions = self.GRADLE_JAVA_VERSIONS.get(gradle_version, self.LATEST_GRADLE_JAVA_VERSIONS)
        #return sorted(set(versions), key=lambda v: [int(i) for i in v.split('.')])

    def determine_java_version(self, folder):
        gradle_version = self.extract_gradle_version(folder)
        if gradle_version:
            versions = self.get_java_versions_from_gradle(gradle_version)
            print(f"Gradle version detected: {gradle_version}")
            print(f"Possible Java versions: {versions}")
            return versions
        else:
            print("Gradle - No Gradle wrapper version found.")
            return self.ALL_JAVA_VERSION_DESC
        
