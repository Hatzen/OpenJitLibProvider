import os
from config import load_properties
from consts import LOCAL_CONFIG_FILE
from build_utils.gradle_utils import GradleUtils
from build_utils.maven_utils import MavenUtils
from config import load_properties
from consts import LOCAL_CONFIG_FILE
from build_utils.build_utils import *

def build(clone_dir):
    project_type = detect_project_type(clone_dir)
    build_tool = MavenUtils()
    if project_type == 'gradle':
        print("detected gradle")
        build_tool = GradleUtils()
    elif project_type == 'maven':
        print("detected maven")
        build_tool = MavenUtils()
    else:
        raise("Project type could not be determined. The folder does not contain Maven or Gradle configuration files.")

    print("update build files..")
    build_tool.update_build_files(clone_dir)

    javaVersions = build_tool.determine_java_version(clone_dir)
    javaVersions.sort(reverse=True) # Use newest version first as it probably contain more features (e.g. security algorithms)
    config = load_properties(LOCAL_CONFIG_FILE)
    stdJava = ""
    for javaVersion in javaVersions:
        fullJavaVersion = '1.' + javaVersion
        stdJava = config['JAVA_HOME'].get(fullJavaVersion)
        print("possible java version" + fullJavaVersion + " " + str(stdJava))
        if stdJava:
            break
    if not stdJava:
        raise Exception("Java version not defined " + str(javaVersions))

    os.environ['JAVA_HOME'] = stdJava
    os.environ['PATH'] = f"{stdJava}\\bin;" + os.environ['PATH']
    print("using java version " + stdJava + " of possible " + str(javaVersions))

    print("build files..")
    build_tool.build_project(clone_dir)
