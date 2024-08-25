import subprocess
import time
import os
import unittest
import shutil

class TestGradleBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Start the Flask server in the background.
        """
        cls.server_process = subprocess.Popen(
            ['gunicorn', '-w', '4', '-b', '0.0.0.0:5000', 'src.app:app'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for the server to start
        time.sleep(5)
    
    @classmethod
    def tearDownClass(cls):
        """
        Terminate the Flask server after the test.
        """
        cls.server_process.terminate()
        cls.server_process.wait()

    def run_gradle_build(self, module, version):
        """
        Run a Gradle build with a specific module and version.
        """
        gradle_wrapper = './gradlew' if os.name != 'nt' else 'gradlew.bat'
        
        # Ensure the `tmp` directory exists
        os.makedirs('tmp', exist_ok=True)
        
        # Define the path for a temporary build script
        build_script_path = 'tmp/build.gradle'
        
        # Write a simple build script that uses the artifact from the Flask server
        with open(build_script_path, 'w') as f:
            f.write(f"""
repositories {{
    maven {{}}
    maven {{
        url 'http://localhost:5000/repository'
    }}
}}

dependencies {{
    implementation 'com.github.{module}:{module}:{version}'
}}
""")

        # Run the Gradle build
        result = subprocess.run([gradle_wrapper, 'build'], capture_output=True, text=True)
        
        # Log the output for debugging
        print(result.stdout)
        print(result.stderr)
        
        return result.returncode == 0

    def test_gradle_build(self):
        """
        Test Gradle build with an artifact from the Flask server.
        """
        module = 'example-module'
        version = '1.0.0'
        
        build_success = self.run_gradle_build(module, version)
        
        self.assertTrue(build_success, "Gradle build failed")

if __name__ == '__main__':
    unittest.main()