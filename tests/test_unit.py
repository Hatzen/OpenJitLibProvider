import os
import sys
import tempfile
import shutil
import unittest
import json

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from config import get_config, load_properties, reload_config
from consts import BASE_DIR
from git_utils import get_repo_url, get_token_for_repo, resolve_dynamic_version
from maven_utils import generate_sha1, generate_md5, generate_pom_file, generate_maven_metadata
from build_utils.build_utils import detect_project_type, getPackagings, getEnding, save_artifact
from build_utils.gradle_utils import GradleUtils
from build_utils.maven_utils import MavenUtils
from app import app

class TestOpenJitUnit(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.client = app.test_client()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_defaults(self):
        cfg = get_config()
        self.assertIn("NEXUS_PORT", cfg)
        self.assertIn("KNOWN_HOSTS", cfg)
        self.assertIn("com.github", cfg["KNOWN_HOSTS"])
        self.assertEqual(cfg["KNOWN_HOSTS"]["com.github"], "github.com")
        self.assertIn("com.gitlab", cfg["KNOWN_HOSTS"])
        self.assertIn("org.bitbucket", cfg["KNOWN_HOSTS"])

    def test_git_repo_url_generation(self):
        # Public repo
        url = get_repo_url("github.com", "Hatzen", "OpenJitLibProvider")
        self.assertEqual(url, "https://github.com/Hatzen/OpenJitLibProvider.git")

        # With explicit token
        url_auth = get_repo_url("github.com", "Hatzen", "SecretRepo", token="my_token_123")
        self.assertEqual(url_auth, "https://my_token_123@github.com/Hatzen/SecretRepo.git")

    def test_dynamic_version_sorting(self):
        # Test helper matching
        resolved = resolve_dynamic_version("https://github.com/nonexistent/dummy.git", "1.0.0")
        self.assertEqual(resolved, "1.0.0")

    def test_maven_checksums(self):
        sample_file = os.path.join(self.temp_dir, "test.jar")
        with open(sample_file, "wb") as f:
            f.write(b"Hello OpenJitLibProvider Maven Artifact!")

        sha1 = generate_sha1(sample_file)
        md5 = generate_md5(sample_file)

        self.assertEqual(len(sha1), 40)
        self.assertEqual(len(md5), 32)

    def test_pom_generation(self):
        pom_path = generate_pom_file(
            group_id="com.github.testorg",
            module="testmodule",
            version="1.2.3",
            packaging="aar",
            artifact_dir=self.temp_dir
        )
        self.assertTrue(os.path.exists(pom_path))
        self.assertTrue(pom_path.endswith("testmodule-1.2.3.pom"))
        self.assertTrue(os.path.exists(f"{pom_path}.sha1"))
        self.assertTrue(os.path.exists(f"{pom_path}.md5"))

        with open(pom_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("<groupId>com.github.testorg</groupId>", content)
        self.assertIn("<artifactId>testmodule</artifactId>", content)
        self.assertIn("<version>1.2.3</version>", content)
        self.assertIn("<packaging>aar</packaging>", content)

    def test_maven_metadata_generation(self):
        generate_maven_metadata(
            group_id="com.github.testorg",
            artifact_id="testmodule",
            version="1.0.0",
            repo_base_path=self.temp_dir
        )
        metadata_file = os.path.join(self.temp_dir, "maven-metadata.xml")
        self.assertTrue(os.path.exists(metadata_file))
        self.assertTrue(os.path.exists(f"{metadata_file}.sha1"))

        with open(metadata_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("<latest>1.0.0</latest>", content)
        self.assertIn("<release>1.0.0</release>", content)

        # Update with new version
        generate_maven_metadata(
            group_id="com.github.testorg",
            artifact_id="testmodule",
            version="1.1.0",
            repo_base_path=self.temp_dir
        )
        with open(metadata_file, "r", encoding="utf-8") as f:
            updated_content = f.read()
        self.assertIn("<latest>1.1.0</latest>", updated_content)
        self.assertIn("<version>1.0.0</version>", updated_content)
        self.assertIn("<version>1.1.0</version>", updated_content)

    def test_detect_project_type(self):
        # Empty folder
        self.assertEqual(detect_project_type(self.temp_dir), 'unknown')

        # Maven project
        with open(os.path.join(self.temp_dir, 'pom.xml'), 'w') as f:
            f.write('<project></project>')
        self.assertEqual(detect_project_type(self.temp_dir), 'maven')
        os.remove(os.path.join(self.temp_dir, 'pom.xml'))

        # Gradle project
        with open(os.path.join(self.temp_dir, 'build.gradle'), 'w') as f:
            f.write('plugins { id "java" }')
        self.assertEqual(detect_project_type(self.temp_dir), 'gradle')

    def test_gradle_utils_versions(self):
        g = GradleUtils()
        # Gradle 4.1 maps to Java 7, 8
        v41 = g.get_java_versions_from_gradle("4.1")
        self.assertIn('8', v41)

        # Gradle 7.4 maps to Java 11..17
        v74 = g.get_java_versions_from_gradle("7.4")
        self.assertIn('17', v74)

        # Gradle 8.5 maps to Java 21
        v85 = g.get_java_versions_from_gradle("8.5")
        self.assertIn('21', v85)

    def test_maven_utils_methods(self):
        m = MavenUtils()
        v = m.get_java_versions_from_maven("3.8.6")
        self.assertIn('17', v)
        self.assertIn('21', v)

    def test_flask_endpoints(self):
        # Dashboard
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"OpenJitLibProvider", res.data)

        # Status JSON API
        res_stats = self.client.get("/api/stats")
        self.assertEqual(res_stats.status_code, 200)
        data = json.loads(res_stats.data)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("artifacts_count", data)

        # Config Reload API
        res_reload = self.client.get("/api/reload_config")
        self.assertEqual(res_reload.status_code, 200)
        reload_data = json.loads(res_reload.data)
        self.assertEqual(reload_data["status"], "success")

        # Repository index
        res_repo = self.client.get("/repository/")
        self.assertEqual(res_repo.status_code, 200)
        self.assertIn(b"Index of", res_repo.data)

if __name__ == '__main__':
    unittest.main()
