import os
import sys
import subprocess
from glob import glob
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH
import xml.etree.ElementTree as ET
import re
from build_utils.build_utils import *


class MavenUtils():

    def build_project(self, clone_dir):
        command ="install"
        
        print("build project in")
        replaced = clone_dir.replace("/",  "\\")
        
        gradlew = os.path.join(os.getcwd(), replaced, "mvnw.cmd")
        gradlew = gradlew.replace("/",  "\\")
        
        print(gradlew)
        process = subprocess.run([gradlew, command], cwd=clone_dir, check=True)

    def update_build_files(self, clone_dir):
        self.replace_jitpack(clone_dir)
        self.remove_Jcenter(clone_dir)

    def replace_jitpack(clone_dir):
        # Replace jitpack when used. May be useful if jitpack is down.
        old_line = '"https://jitpack.io"'
        new_line = '"http://127.0.0.1:5000/repository"'
        replace_in_file(os.path.join(clone_dir, 'pom.xml'), old_line, new_line)

    def remove_Jcenter(clone_dir):
        build_gradle = os.path.join(clone_dir, 'pom.xml')

        remove_line_with_partial_match(build_gradle, "com.novoda:bintray-release")
        remove_line_with_partial_match(build_gradle, "com.jfrog.bintray.gradle:gradle-bintray-plugin")
        



    ALL_JAVA_VERSION_DESC = ['21', '17','11','8' ]

    MAVEN_JAVA_VERSIONS = {
        '3.9.0': ['8', '11', '17', '21'],
        '3.8.6': ['8', '11', '17', '21'],
        '3.8.5': ['8', '11', '17', '21'],
        '3.8.4': ['8', '11', '17', '21'],
        '3.8.3': ['8', '11', '17', '21'],
        '3.8.2': ['8', '11', '17', '21'],
        '3.8.1': ['8', '11', '17', '21'],
        '3.8.0': ['8', '11', '17', '21'],
        '3.7.0': ['8', '11', '17'],
        '3.6.3': ['8', '11'],
        '3.6.2': ['8', '11'],
        '3.6.1': ['8', '11'],
        '3.6.0': ['8', '11'],
        '3.5.4': ['7', '9'],
        '3.5.3': ['7', '9'],
        '3.5.2': ['7', '9'],
        '3.5.1': ['7', '9'],
        '3.5.0': ['7', '9'],
        '3.4.0': ['7', '8'],
        '3.3.9': ['7', '8'],
        '3.3.8': ['7', '8'],
        '3.3.7': ['7', '8'],
        '3.3.6': ['7', '8'],
        '3.3.5': ['7', '8'],
        '3.3.4': ['7', '8'],
        '3.3.3': ['7', '8'],
        '3.3.2': ['7', '8'],
        '3.3.1': ['7', '8'],
        '3.3.0': ['7', '8'],
        '3.2.5': ['7'],
        '3.2.4': ['7'],
        '3.2.3': ['7'],
        '3.2.2': ['7'],
        '3.2.1': ['7'],
        '3.2.0': ['7']
    }

    # Fallback-Werte für die neueste bekannte Version
    LATEST_GRADLE_JAVA_VERSIONS = ['17', '21']
    LATEST_MAVEN_JAVA_VERSIONS = ['8', '11', '17', '21']

    def extract_maven_version(folder):
        """Extract the Maven version from maven-wrapper.properties."""
        wrapper_properties_file = os.path.join(folder, 'mvn', 'wrapper', 'maven-wrapper.properties')
        if os.path.exists(wrapper_properties_file):
            with open(wrapper_properties_file, 'r') as file:
                content = file.read()
            match = re.search(r'distributionUrl=.*apache-maven-(\d+\.\d+\.\d+)-bin\.zip', content)
            if match:
                return match.group(1)
        return None

    def get_java_versions_from_maven(self, maven_version):
        """Get the possible Java versions supported by the Maven version with fallback to latest version."""
        versions = self.MAVEN_JAVA_VERSIONS.get(maven_version, self.LATEST_MAVEN_JAVA_VERSIONS)
        return sorted(set(versions), key=lambda v: [int(i) for i in v.split('.')])

    def determine_java_version(self, folder):
        maven_version = self.extract_maven_version(folder)
        if maven_version:
            versions = self.get_java_versions_from_maven(maven_version)
            print(f"Maven version detected: {maven_version}")
            print(f"Possible Java versions: {versions}")
            return versions
        else:
            print("Maven - No Maven wrapper version found.")
            return self.ALL_JAVA_VERSION_DESC
        
