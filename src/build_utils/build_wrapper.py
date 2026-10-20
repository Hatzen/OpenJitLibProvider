import os
import sys
from config import get_config
from build_utils.gradle_utils import GradleUtils
from build_utils.maven_utils import MavenUtils
from build_utils.build_utils import detect_project_type

def resolve_java_path(java_versions, config):
    """
    Finds the best matching JAVA_HOME from config or system environment.
    Supports versions formatted as '8', '11', '17', '21' or '1.8', '1.11', etc.
    """
    java_home_map = config.get('JAVA_HOME') or {}

    for v in java_versions:
        v_str = str(v)
        candidates = [
            v_str,
            f"1.{v_str}",
            v_str.replace("1.", "")
        ]
        for c in candidates:
            if c in java_home_map and java_home_map[c]:
                return java_home_map[c]

    # If not found in specific versions, check any configured JAVA_HOME
    if java_home_map:
        first_configured = next(iter(java_home_map.values()), None)
        if first_configured:
            return first_configured

    # Fallback to system environment JAVA_HOME
    env_java = os.environ.get('JAVA_HOME')
    if env_java and os.path.exists(env_java):
        return env_java

    return None

def build(clone_dir, target_module=None):
    """Detects project type, updates build files, configures Java environment, and executes build."""
    project_type = detect_project_type(clone_dir)
    if project_type == 'gradle':
        print(f"Detected Gradle project in {clone_dir}")
        build_tool = GradleUtils()
    elif project_type == 'maven':
        print(f"Detected Maven project in {clone_dir}")
        build_tool = MavenUtils()
    else:
        raise Exception(f"Project type could not be determined for {clone_dir}. Neither pom.xml nor build.gradle found.")

    print("Updating build files...")
    build_tool.update_build_files(clone_dir)

    raw_versions = build_tool.determine_java_version(clone_dir)
    # Sort versions descending (prefer newer Java if compatible)
    java_versions = []
    for x in raw_versions:
        try:
            java_versions.append(int(str(x).replace("1.", "")))
        except ValueError:
            pass
    java_versions.sort(reverse=True)

    config = get_config()
    selected_java = resolve_java_path(java_versions, config)

    if selected_java and os.path.exists(selected_java):
        os.environ['JAVA_HOME'] = selected_java
        bin_dir = os.path.join(selected_java, 'bin')
        os.environ['PATH'] = f"{bin_dir}{os.pathsep}" + os.environ.get('PATH', '')
        print(f"Using JAVA_HOME: {selected_java}")
    else:
        print("Using system default Java environment.")

    print(f"Building project (target module: {target_module or 'all'})...")
    build_tool.build_project(clone_dir, target_module=target_module)

