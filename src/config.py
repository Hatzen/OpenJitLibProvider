import os
import yaml
from consts import BASE_DIR, LOCAL_CONFIG_FILE

_cached_config = None

DEFAULT_KNOWN_HOSTS = {
    "com.github": "github.com",
    "com.gitlab": "gitlab.com",
    "org.bitbucket": "bitbucket.org",
    "com.gitee": "gitee.com",
    "com.azure": "dev.azure.com",
}

def find_config_file(file_path=None):
    candidates = [
        file_path,
        os.path.join(BASE_DIR, file_path) if file_path else None,
        os.path.join(BASE_DIR, LOCAL_CONFIG_FILE),
        os.path.join(BASE_DIR, "src", "config.yml"),
        os.path.join(BASE_DIR, "config-local-example.yml"),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None

def load_properties(file_path=None):
    global _cached_config
    config_file = find_config_file(file_path or LOCAL_CONFIG_FILE)
    config = {}

    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file) or {}
            print(f"Loaded config from: {config_file}")
        except Exception as e:
            print(f"Error reading config {config_file}: {e}")

    # Set defaults
    if "NEXUS_PORT" not in config:
        config["NEXUS_PORT"] = int(os.environ.get("PORT", os.environ.get("NEXUS_PORT", 5000)))
    else:
        config["NEXUS_PORT"] = int(config["NEXUS_PORT"])

    if "KNOWN_HOSTS" not in config or not config["KNOWN_HOSTS"]:
        config["KNOWN_HOSTS"] = DEFAULT_KNOWN_HOSTS.copy()
    else:
        # Merge with defaults
        merged_hosts = DEFAULT_KNOWN_HOSTS.copy()
        merged_hosts.update(config["KNOWN_HOSTS"])
        config["KNOWN_HOSTS"] = merged_hosts

    if "REPOSITORY_TOKENS" not in config or not isinstance(config["REPOSITORY_TOKENS"], dict):
        config["REPOSITORY_TOKENS"] = {}

    if "JAVA_HOME" not in config or not isinstance(config["JAVA_HOME"], dict):
        config["JAVA_HOME"] = {}

    if "ANDROID_SDK_ROOT" not in config:
        config["ANDROID_SDK_ROOT"] = os.environ.get("ANDROID_SDK_ROOT", os.environ.get("ANDROID_HOME", ""))

    if "DELETE_ARTIFACTS" not in config:
        config["DELETE_ARTIFACTS"] = -1
    if "DELETE_TMP" not in config:
        config["DELETE_TMP"] = -1

    _cached_config = config
    return config

def get_config():
    global _cached_config
    if _cached_config is None:
        _cached_config = load_properties()
    return _cached_config

def reload_config():
    return load_properties()