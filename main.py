import os
import subprocess
from flask import Flask, request, send_file, abort
from glob import glob
import datetime
import hashlib

# Konfiguration
LOCAL_REPO_PATH = "repo/"

app = Flask(__name__)

def get_github_repo_url(organization, module):
    return f"https://github.com/{organization}/{module}.git"

def clone_and_checkout(repo_url, version, clone_dir):
    # print(os.listdir(clone_dir))
    if(len(os.listdir(clone_dir)) == 0):
        subprocess.run(["git", "clone", repo_url, clone_dir], check=True)
    # subprocess.run(["git", "-C", clone_dir, "checkout", version], check=True)
    if(version != "master"):
        checkout_tag(clone_dir, version)


def checkout_tag(repo_dir, tag):
    try:
        run_command(['git', 'checkout', f'tags/{tag}'], cwd=repo_dir)
    # Some repos like https://github.com/skydoves/ElasticViews prefixes the version tag with "v"
    except:
        run_command(['git', 'checkout', f'tags/v{tag}'], cwd=repo_dir)


def run_command(command, cwd=None):
    try:
        result = subprocess.run(
            command,
            cwd=cwd, 
            shell=True,
            check=True,        # Löst eine CalledProcessError aus, wenn der Befehl fehlschlägt
            stdout=subprocess.PIPE,  # Fängt die Standardausgabe ab
            stderr=subprocess.PIPE,  # Fängt die Standardfehlerausgabe ab
            text=True            # Gibt die Ausgabe als String statt als Bytes zurück
        )
        print("Errors:", result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command {command} failed with error: {e}")
        raise

def replace_line_in_file(file_path, old_line, new_line):
    with open(file_path, 'r') as file:
        content = file.read().replace(old_line, new_line)
    with open(file_path, 'w') as file:
        file.write(content)

def build_project(clone_dir):
    #print(clone_dir)
    #print(os.listdir(clone_dir))
    subprocess.run(["gradlew.bat", "assembleRelease"], cwd=clone_dir, check=True, shell=True)
    # subprocess.run(["gradlew.bat", "clean", "build"], cwd=clone_dir, check=True)
    # subprocess.run(["./gradlew", "clean", "build"], cwd=clone_dir, check=True)

def handle_artifact_request(organization, module, version):
    repo_url = get_github_repo_url(organization, module)
    clone_dir = os.path.join("tmp/", f"{module}-{version}")
    
    if not os.path.exists(clone_dir):
        os.makedirs(clone_dir)
        
    try:
        clone_and_checkout(repo_url, version, clone_dir)
        
        if (os.path.exists(clone_dir + "/build")):
            print("build exists skip: " + clone_dir)
            return
        
        # remove jitpack
        old_line = '"https://jitpack.io"'
        new_line = '"http://127.0.0.1:5000/repository"'
        replace_line_in_file(clone_dir + '/build.gradle', old_line, new_line)
        replace_line_in_file(clone_dir + '/settings.gradle', old_line, new_line)

        build_project(clone_dir)
        
        # jar_file = os.path.join(clone_dir, "build", "libs", f"{module}-{version}.jar")
        for filename in glob(clone_dir + '/**/*.aar', recursive=True):
            print(filename)
            jar_file = filename
        
        if os.path.exists(jar_file):
            group_path = organization.replace('.', '/')
            dest_dir = os.path.join(LOCAL_REPO_PATH, group_path, module, version)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
                
            dest_file = os.path.join(dest_dir, f"{module}-{version}.aar")
            # TODO: get proper file name
            # dest_file = os.path.join(dest_dir, f"{module}-{version}.jar")
            os.rename(jar_file, dest_file)

            print("generate maven files " + clone_dir)
            generate_maven_metadata(organization, module, version)
            generate_pom_file(organization, module, version)

            return dest_file
        else:
            print("aar not found: " + clone_dir)
            return None
    finally:
        # subprocess.run(["rm", "-rf", clone_dir])
        pass


def generate_maven_metadata(organization, module, version):
    group_path = organization.replace('.', '/')
    artifact_dir = os.path.join(LOCAL_REPO_PATH, group_path, module)
    
    metadata_path = os.path.join(artifact_dir, "maven-metadata.xml")
    if not os.path.exists(metadata_path):

        last_updated = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        metadata_content = f"""<?xml version="1.0" encoding="UTF-8"?>
        <metadata>
            <groupId>{organization}</groupId>
            <artifactId>{module}</artifactId>
            <versioning>
                <latest>{version}</latest>
                <release>{version}</release>
                <versions>
                    <version>{version}</version>
                </versions>
                <lastUpdated>{last_updated}</lastUpdated>
            </versioning>
        </metadata>"""
        
        with open(metadata_path, "w") as f:
            f.write(metadata_content)


def generate_pom_file(organization, module, version):
    group_path = organization.replace('.', '/')
    artifact_dir = os.path.join(LOCAL_REPO_PATH, group_path, module, version)

    pom_file_path = os.path.join(artifact_dir, f"{module}-{version}.pom")
    if not os.path.exists(pom_file_path):
        pom_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.github.{organization}</groupId>
    <artifactId>{module}</artifactId>
    <version>{version}</version>
    <packaging>aar</packaging>

    <name>{module}</name>
    <description>Auto-generated POM for {module}</description>
</project>"""

        with open(pom_file_path, "w") as f:
            f.write(pom_content)
        
        write_sha1_to_file(pom_file_path)

def generate_sha1(file_path):
    """Generate SHA-1 hash for the given file."""
    sha1 = hashlib.sha1()
    try:
        with open(file_path, 'rb') as file:
            while chunk := file.read(8192):
                sha1.update(chunk)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except IOError as e:
        print(f"IO error occurred: {e}")
        return None
    
    return sha1.hexdigest()

def write_sha1_to_file(pom_file_path):
    """Write the SHA-1 hash to a .sha1 file."""
    sha1_hash = generate_sha1(pom_file_path)
    sha1_file_path = f"{pom_file_path}.sha1"
    with open(sha1_file_path, 'w') as sha1_file:
        sha1_file.write(sha1_hash + '\n')

@app.route("/repository/<path:artifact_path>", methods=["GET"])
def repository(artifact_path: str):

    if (artifact_path.find("com/github/") == -1): 
        abort(404, "No github url")

    artifact_path = artifact_path.replace("com/github/", "")
    parts = artifact_path.split('/')

    if len(parts) < 4:
        abort(400, "Ungültige Artefakt-URL")
    if len(parts) > 4:
        # Problem appeared after replacing jitpack in dependency projects, dependency might be available by maven, but repo order might priorize this repo. 
        # avoid providing /repository/com/github/traex/rippleeffect/ripple/1.3.1-OG/ripple-1.3.1-OG.pom [HEAD]
        abort(404, "Ungültige Artefakt-URL. Zu viele module?")

    organization = parts[0]
    module = parts[1]
    version = parts[2]
    # TODO: Remove snapshot or support usefully?
    version = version.replace("-SNAPSHOT", "")
    file_name = parts[-1]


    print(artifact_path)
    # print("organization")
    # print(organization)
    # print("module")
    # print(module)
    # print(version)
    # print(file_name)


    # parts = line.split(':')
    # if len(parts) != 3:
    #     print(f"Invalid line format: {line}")
    #     return

    # group, name, version = parts
    # group = group.replace('com.github.', '')
    # repo_url = f"https://github.com/{group.replace('.', '/')}/{name}.git"

    # /repository/ch/acra/acra-core/5.0.2/acra-core-5.0.2.pom HTTP/1.1
    
    artifact_dir = os.path.join(LOCAL_REPO_PATH, organization, module, version)
    artifact_file = os.path.join(artifact_dir, file_name)
    
    if not os.path.exists(artifact_file):
        print("generate artifacts")
        artifact_file = handle_artifact_request(organization, module, version)
    
    if artifact_file and os.path.exists(artifact_file):
        return send_file(artifact_file)
    else:
        abort(404, "Artefakt nicht gefunden")

if __name__ == "__main__":
    # java_home_path = "C:/Program Files/Java/jdk-11.0.2/"  # Setze den Pfad zu deiner Java-Installation
    java_home_path = "C:/Program Files/Java/openlogic-openjdk-8u422-b05-windows-x64/"
    os.environ['JAVA_HOME'] = java_home_path
    os.environ['PATH'] = java_home_path + "\\bin;" + os.environ['PATH']
    os.environ['ANDROID_SDK_ROOT'] = "C:/Users/kaiha/AppData/Local/Android/Sdk"
    os.environ['ANDROID_HOME'] = "C:/Users/kaiha/AppData/Local/Android/Sdk" # Needed for old gradle wrapper 4.1
    
    app.run(host="0.0.0.0", port=5000)







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


'''
TODO: consider adding further hashes

build exists skip: tmp/ProfilePictureGenerator-0.7.2b
127.0.0.1 - - [25/Aug/2024 18:12:31] "GET /repository/com/github/Hatzen/ProfilePictureGenerator/0.7.2b/ProfilePictureGenerator-0.7.2b.aar.sha1 HTTP/1.1" 404 -        
Hatzen/ProfilePictureGenerator/0.7.2b/ProfilePictureGenerator-0.7.2b.aar
127.0.0.1 - - [25/Aug/2024 18:12:31] "GET /repository/com/github/Hatzen/ProfilePictureGenerator/0.7.2b/ProfilePictureGenerator-0.7.2b.aar HTTP/1.1" 200 -
Hatzen/ProfilePictureGenerator/0.7.2b/ProfilePictureGenerator-0.7.2b-sources.jar
generate artifacts
Errors:
build exists skip: tmp/ProfilePictureGenerator-0.7.2b
127.0.0.1 - - [25/Aug/2024 18:12:31] "HEAD /repository/com/github/Hatzen/ProfilePictureGenerator/0.7.2b/ProfilePictureGenerator-0.7.2b-sources.jar HTTP/1.1" 404 -    
Hatzen/ProfilePictureGenerator/0.7.2b/ProfilePictureGenerator-0.7.2b-javadoc.jar
generate artifacts
Errors:
build exists skip: tmp/ProfilePictureGenerator-0.7.2b
127.0.0.1 - - [25/Aug/2024 18:12:31] "HEAD /repository/com/github/Hatzen/ProfilePictureGenerator/0.7.2b/ProfilePictureGenerator-0.7.2b-javadoc.jar HTTP/1.1" 404 -    


'''