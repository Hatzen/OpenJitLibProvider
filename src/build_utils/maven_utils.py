import os
import sys
import subprocess
import re
from build_utils.build_utils import (
    remove_line_with_partial_match,
    replace_in_file
)

class MavenUtils:

    ALL_JAVA_VERSION_DESC = ['21', '17', '11', '8']

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
        '3.5.4': ['7', '8', '9'],
        '3.5.0': ['7', '8', '9'],
        '3.3.9': ['7', '8'],
    }

    LATEST_MAVEN_JAVA_VERSIONS = ['8', '11', '17', '21']

    def get_mvnw_path(self, clone_dir):
        """Locates the Maven wrapper executable, falling back to system 'mvn'."""
        if os.name == 'nt':
            for name in ["mvnw.cmd", "mvnw.bat"]:
                candidate = os.path.join(clone_dir, name)
                if os.path.exists(candidate):
                    return candidate
        else:
            candidate = os.path.join(clone_dir, "mvnw")
            if os.path.exists(candidate):
                try:
                    os.chmod(candidate, 0o755)
                except Exception as e:
                    print(f"Could not chmod mvnw: {e}")
                return candidate

        return "mvn"

    def build_project(self, clone_dir, target_module=None):
        mvn_cmd = self.get_mvnw_path(clone_dir)
        args = [mvn_cmd, "clean", "install", "-DskipTests=true", "-Dmaven.javadoc.skip=true"]

        if target_module and target_module != ".":
            args.extend(["-pl", target_module, "-am"])

        print(f"Running Maven build: {' '.join(args)} in {clone_dir}")
        result = subprocess.run(args, cwd=clone_dir, capture_output=True)
        sys.stdout.write(result.stdout.decode('utf-8', errors='replace'))
        sys.stderr.write(result.stderr.decode('utf-8', errors='replace'))

        if result.returncode != 0:
            raise Exception(f"Maven build failed with exit code {result.returncode}")

    def update_build_files(self, clone_dir):
        self.replace_jitpack(clone_dir)
        self.remove_Jcenter(clone_dir)

    def replace_jitpack(self, clone_dir):
        pom_path = os.path.join(clone_dir, 'pom.xml')
        old_line = 'https://jitpack.io'
        new_line = 'http://127.0.0.1:5000/repository'
        replace_in_file(pom_path, old_line, new_line)

    def remove_Jcenter(self, clone_dir):
        pom_path = os.path.join(clone_dir, 'pom.xml')
        # Replace jcenter URL in pom if present
        replace_in_file(pom_path, 'https://jcenter.bintray.com', 'https://repo.maven.apache.org/maven2')
        replace_in_file(pom_path, 'http://jcenter.bintray.com', 'https://repo.maven.apache.org/maven2')

    def extract_maven_version(self, folder):
        """Extract the Maven version from maven-wrapper.properties (.mvn/wrapper or mvn/wrapper)."""
        candidates = [
            os.path.join(folder, '.mvn', 'wrapper', 'maven-wrapper.properties'),
            os.path.join(folder, 'mvn', 'wrapper', 'maven-wrapper.properties'),
        ]
        for wrapper_file in candidates:
            if os.path.exists(wrapper_file):
                try:
                    with open(wrapper_file, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                    match = re.search(r'apache-maven-(\d+\.\d+\.\d+)', content)
                    if match:
                        return match.group(1)
                except Exception as e:
                    print(f"Error reading maven wrapper properties: {e}")
        return None

    def get_java_versions_from_maven(self, maven_version):
        versions = self.MAVEN_JAVA_VERSIONS.get(maven_version, self.LATEST_MAVEN_JAVA_VERSIONS)
        return sorted(set(versions), key=lambda v: [int(i) for i in v.split('.')])

    def determine_java_version(self, folder):
        maven_version = self.extract_maven_version(folder)
        if maven_version:
            versions = self.get_java_versions_from_maven(maven_version)
            print(f"Maven version detected: {maven_version}, possible Java versions: {versions}")
            return versions
        else:
            return self.ALL_JAVA_VERSION_DESC

        
