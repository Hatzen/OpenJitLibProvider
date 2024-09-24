import os
import datetime
import hashlib
from consts import LOCAL_CLONE_PATH, LOCAL_REPO_PATH

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime


def generate_maven_metadata(organization, repo, version):
    group_path = organization.replace('.', '/')
    artifact_dir = os.path.join(LOCAL_REPO_PATH, group_path, repo)
    
    metadata_path = os.path.join(artifact_dir, "maven-metadata.xml")


    # Example parameters
    group_id = organization # "com.github.test-repo"
    artifact_id = repo # "module"
    # TODO: Check if we get the Snapshot postfix here already.
    is_snapshot = "SNAPSHOT" in version  # Automatically detect if it's a snapshot version
    
    # Create or update the metadata file
    create_or_update_metadata_file(group_id, artifact_id, version, metadata_path, is_snapshot)

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


def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def create_or_update_metadata_file(group_id, artifact_id, version, metadata_path, is_snapshot=False):
    """Creates or updates a maven-metadata.xml file with a new version."""
    
    # Check if metadata file exists
    if os.path.exists(metadata_path):
        # Load the existing metadata file
        tree = ET.parse(metadata_path)
        root = tree.getroot()
    else:
        # Create a new metadata XML structure
        root = ET.Element("metadata")
        group_id_element = ET.SubElement(root, "groupId")
        group_id_element.text = group_id

        artifact_id_element = ET.SubElement(root, "artifactId")
        artifact_id_element.text = artifact_id

        versioning = ET.SubElement(root, "versioning")
        latest = ET.SubElement(versioning, "latest")
        release = ET.SubElement(versioning, "release")
        versions = ET.SubElement(versioning, "versions")
        last_updated = ET.SubElement(versioning, "lastUpdated")

    versioning = root.find("versioning")

    # Handle snapshot versions
    if is_snapshot and "SNAPSHOT" in version:
        snapshot_element = versioning.find("snapshot")
        if snapshot_element is None:
            snapshot_element = ET.SubElement(versioning, "snapshot")
        
        # Set timestamp and build number
        timestamp = datetime.utcnow().strftime('%Y%m%d.%H%M%S')
        build_number = "1"  # This could be incremented based on custom logic

        timestamp_element = snapshot_element.find("timestamp")
        if timestamp_element is None:
            timestamp_element = ET.SubElement(snapshot_element, "timestamp")
        timestamp_element.text = timestamp

        build_number_element = snapshot_element.find("buildNumber")
        if build_number_element is None:
            build_number_element = ET.SubElement(snapshot_element, "buildNumber")
        build_number_element.text = build_number

        # Add to snapshotVersions
        snapshot_versions = versioning.find("snapshotVersions")
        if snapshot_versions is None:
            snapshot_versions = ET.SubElement(versioning, "snapshotVersions")

        jar_snapshot_version = ET.SubElement(snapshot_versions, "snapshotVersion")
        extension = ET.SubElement(jar_snapshot_version, "extension")
        extension.text = "jar"
        value = ET.SubElement(jar_snapshot_version, "value")
        value.text = f"{version.replace('SNAPSHOT', '')}-{timestamp}-{build_number}"
        updated = ET.SubElement(jar_snapshot_version, "updated")
        updated.text = datetime.utcnow().strftime('%Y%m%d%H%M%S')

        pom_snapshot_version = ET.SubElement(snapshot_versions, "snapshotVersion")
        extension_pom = ET.SubElement(pom_snapshot_version, "extension")
        extension_pom.text = "pom"
        value_pom = ET.SubElement(pom_snapshot_version, "value")
        value_pom.text = f"{version.replace('SNAPSHOT', '')}-{timestamp}-{build_number}"
        updated_pom = ET.SubElement(pom_snapshot_version, "updated")
        updated_pom.text = datetime.utcnow().strftime('%Y%m%d%H%M%S')

    # Handle regular (non-SNAPSHOT) versions
    else:
        # Update latest and release versions for non-SNAPSHOT
        versioning.find("latest").text = version
        versioning.find("release").text = version

        # Check if the version already exists
        versions = versioning.find("versions")
        if version not in [v.text for v in versions.findall("version")]:
            new_version = ET.SubElement(versions, "version")
            new_version.text = version

    # Update the last updated timestamp
    now = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    versioning.find("lastUpdated").text = now

    # Pretty-print and save the XML
    with open(metadata_path, "w") as f:
        f.write(prettify_xml(root))