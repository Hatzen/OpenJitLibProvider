import os
import sys

# Ensure src directory is on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from config import get_config
from cron_cleaner import startCronCleaner
from app import app

def initialize_environment():
    config = get_config()

    # Determine default Java version if configured
    java_homes = config.get('JAVA_HOME') or {}
    std_java = java_homes.get('1.8') or java_homes.get('8')

    if not std_java and java_homes:
        std_java = next(iter(java_homes.values()), None)

    if std_java and os.path.exists(std_java):
        os.environ['JAVA_HOME'] = std_java
        bin_dir = os.path.join(std_java, 'bin')
        os.environ['PATH'] = f"{bin_dir}{os.pathsep}" + os.environ.get('PATH', '')
        print(f"Default Java configured: {std_java}")
    elif os.environ.get('JAVA_HOME'):
        print(f"Using system JAVA_HOME: {os.environ.get('JAVA_HOME')}")
    else:
        print("No specific Java path configured; using system PATH.")

    sdk_root = config.get('ANDROID_SDK_ROOT')
    if sdk_root and os.path.exists(sdk_root):
        os.environ['ANDROID_SDK_ROOT'] = sdk_root
        os.environ['ANDROID_HOME'] = sdk_root

    startCronCleaner()

initialize_environment()

if __name__ == '__main__':
    cfg = get_config()
    port = int(cfg.get('NEXUS_PORT', 5000))
    print(f"Starting OpenJitLibProvider server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)