import os
import hashlib
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from consts import LOCAL_REPO_PATH

def generate_sha1(file_path: str) -> str:
    """Generates SHA1 checksum for a file."""
    sha1 = hashlib.sha1()
    try:
        with open(file_path, 'rb') as file:
            while chunk := file.read(8192):
                sha1.update(chunk)
        return sha1.hexdigest()
    except (FileNotFoundError, IOError) as e:
        print(f"Error generating SHA1 for {file_path}: {e}")
        return ""

def generate_md5(file_path: str) -> str:
    """Generates MD5 checksum for a file."""
    md5 = hashlib.md5()
    try:
        with open(file_path, 'rb') as file:
            while chunk := file.read(8192):
                md5.update(chunk)
        return md5.hexdigest()
    except (FileNotFoundError, IOError) as e:
        print(f"Error generating MD5 for {file_path}: {e}")
        return ""

def write_checksums_for_file(file_path: str):
    """Writes both .sha1 and .md5 checksum files."""
    sha1 = generate_sha1(file_path)
    if sha1:
        with open(f"{file_path}.sha1", 'w', encoding='utf-8') as f:
            f.write(sha1 + '\n')

    md5 = generate_md5(file_path)
    if md5:
        with open(f"{file_path}.md5", 'w', encoding='utf-8') as f:
            f.write(md5 + '\n')

def generate_maven_metadata(group_id: str, artifact_id: str, version: str, repo_base_path: str = None):
    """Generates or updates maven-metadata.xml in the artifact directory."""
    if repo_base_path is None:
        group_path = group_id.replace('.', os.sep).replace('/', os.sep)
        artifact_dir = os.path.join(LOCAL_REPO_PATH, group_path, artifact_id)
    else:
        artifact_dir = repo_base_path

    os.makedirs(artifact_dir, exist_ok=True)
    metadata_path = os.path.join(artifact_dir, "maven-metadata.xml")
    is_snapshot = "SNAPSHOT" in version

    create_or_update_metadata_file(group_id, artifact_id, version, metadata_path, is_snapshot)
    write_checksums_for_file(metadata_path)

def generate_pom_file(group_id: str, module: str, version: str, packaging: str = "jar", artifact_dir: str = None):
    """Generates a standard POM file and corresponding SHA1 and MD5 checksums."""
    if artifact_dir is None:
        group_path = group_id.replace('.', os.sep).replace('/', os.sep)
        artifact_dir = os.path.join(LOCAL_REPO_PATH, group_path, module, version)

    os.makedirs(artifact_dir, exist_ok=True)
    clean_packaging = packaging.lstrip('.').lower() if packaging else "jar"
    pom_file_path = os.path.join(artifact_dir, f"{module}-{version}.pom")

    pom_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>{group_id}</groupId>
    <artifactId>{module}</artifactId>
    <version>{version}</version>
    <packaging>{clean_packaging}</packaging>
    <name>{module}</name>
    <description>Artifact provided by OpenJitLibProvider for {module}</description>
</project>
"""
    with open(pom_file_path, "w", encoding='utf-8') as f:
        f.write(pom_content)

    write_checksums_for_file(pom_file_path)
    return pom_file_path

def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def create_or_update_metadata_file(group_id, artifact_id, version, metadata_path, is_snapshot=False):
    """Creates or updates a maven-metadata.xml file with a new version."""
    if os.path.exists(metadata_path):
        try:
            tree = ET.parse(metadata_path)
            root = tree.getroot()
        except Exception:
            root = ET.Element("metadata")
    else:
        root = ET.Element("metadata")

    if root.find("groupId") is None:
        group_id_element = ET.SubElement(root, "groupId")
        group_id_element.text = group_id
    else:
        root.find("groupId").text = group_id

    if root.find("artifactId") is None:
        artifact_id_element = ET.SubElement(root, "artifactId")
        artifact_id_element.text = artifact_id
    else:
        root.find("artifactId").text = artifact_id

    versioning = root.find("versioning")
    if versioning is None:
        versioning = ET.SubElement(root, "versioning")

    latest = versioning.find("latest")
    if latest is None:
        latest = ET.SubElement(versioning, "latest")
    latest.text = version

    release = versioning.find("release")
    if release is None:
        release = ET.SubElement(versioning, "release")
    if not is_snapshot:
        release.text = version

    versions = versioning.find("versions")
    if versions is None:
        versions = ET.SubElement(versioning, "versions")

    existing_versions = [v.text for v in versions.findall("version")]
    if version not in existing_versions:
        new_version = ET.SubElement(versions, "version")
        new_version.text = version

    if is_snapshot:
        snapshot_element = versioning.find("snapshot")
        if snapshot_element is None:
            snapshot_element = ET.SubElement(versioning, "snapshot")

        now_utc = datetime.utcnow()
        timestamp = now_utc.strftime('%Y%m%d.%H%M%S')
        build_number = "1"

        timestamp_element = snapshot_element.find("timestamp")
        if timestamp_element is None:
            timestamp_element = ET.SubElement(snapshot_element, "timestamp")
        timestamp_element.text = timestamp

        build_number_element = snapshot_element.find("buildNumber")
        if build_number_element is None:
            build_number_element = ET.SubElement(snapshot_element, "buildNumber")
        build_number_element.text = build_number

    now = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    last_updated = versioning.find("lastUpdated")
    if last_updated is None:
        last_updated = ET.SubElement(versioning, "lastUpdated")
    last_updated.text = now

    with open(metadata_path, "w", encoding='utf-8') as f:
        f.write(prettify_xml(root))