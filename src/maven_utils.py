import os
import datetime
import hashlib
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH

def generate_maven_metadata(organization, repo, version):
    group_path = organization.replace('.', '/')
    artifact_dir = os.path.join(LOCAL_REPO_PATH, group_path, repo)
    
    metadata_path = os.path.join(artifact_dir, "maven-metadata.xml")
    if not os.path.exists(metadata_path):
        last_updated = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        # TODO: Need proper versioning for different versions
        metadata_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<metadata>
    <groupId>{organization}</groupId>
    <artifactId>{repo}</artifactId>
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

def generate_pom_file(organization, module, version, packaging):
    group_path = organization.replace('.', '/')
    artifact_dir = os.path.join(LOCAL_REPO_PATH, group_path, module, version)

    pom_file_path = os.path.join(artifact_dir, f"{module}-{version}{packaging}.pom")
    
    if not os.path.exists(pom_file_path):
        pom_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
<modelVersion>4.0.0</modelVersion>
<groupId>com.github.{organization}</groupId>
<artifactId>{module}</artifactId>
<version>{version}</version>
<packaging>{packaging}</packaging>
<name>{module}</name>
<description>Auto-generated POM for {module}</description>
</project>"""
    
        with open(pom_file_path, "w") as f:
            f.write(pom_content)
            
            write_sha1_to_file(pom_file_path)

def generate_sha1(file_path):
    sha1 = hashlib.sha1()
    try:
        with open(file_path, 'rb') as file:
            while chunk := file.read(8192):
                sha1.update(chunk)
    except (FileNotFoundError, IOError) as e:
        print(f"Error generating SHA1 for {file_path}: {e}")
        return None
    
    return sha1.hexdigest()

def write_sha1_to_file(pom_file_path):
    sha1_hash = generate_sha1(pom_file_path)
    if sha1_hash:
        sha1_file_path = f"{pom_file_path}.sha1"
        with open(sha1_file_path, 'w') as sha1_file:
            sha1_file.write(sha1_hash + '\n')