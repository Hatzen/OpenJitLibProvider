
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_REPO_PATH = os.environ.get("OPENJIT_REPO_PATH", os.path.join(BASE_DIR, "repo"))
LOCAL_CLONE_PATH = os.environ.get("OPENJIT_TMP_PATH", os.path.join(BASE_DIR, "tmp"))
LOCAL_LOGS_PATH = os.environ.get("OPENJIT_LOGS_PATH", os.path.join(BASE_DIR, "logs"))
LOCAL_CONFIG_FILE = os.environ.get("OPENJIT_CONFIG_FILE", "config.yml")