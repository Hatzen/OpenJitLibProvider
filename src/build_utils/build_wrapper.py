import os
import sys
import subprocess
from glob import glob
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH
import xml.etree.ElementTree as ET
import re
from config import load_properties
from consts import LOCAL_CONFIG_FILE
from build_utils.gradle_utils import GradleUtils
from build_utils.maven_utils import MavenUtils
from config import load_properties
from consts import LOCAL_CONFIG_FILE
from build_utils import *

def build(clone_dir):
    project_type = detect_project_type(clone_dir)
    build_tool = MavenUtils()
    if project_type == 'gradle':
        build_tool = GradleUtils()
    elif project_type == 'maven':
        build_tool = MavenUtils()
    else:
        raise("Project type could not be determined. The folder does not contain Maven or Gradle configuration files.")

    javaVersion = build_tool.determine_java_version(clone_dir)
    config = load_properties(LOCAL_CONFIG_FILE)
    stdJava = config['JAVA_HOME']['1.' + javaVersion]
    os.environ['JAVA_HOME'] = stdJava
    os.environ['PATH'] = f"{stdJava}\\bin;" + os.environ['PATH']

    print("update build files..")
    build_tool.update_build_files(clone_dir)
    
    if os.path.exists(os.path.join(clone_dir, "build")):
        print("build files exist not building again")
        return # check commit hash and remove build dir.

    print("build files..")
    build_tool.build_project(clone_dir)
