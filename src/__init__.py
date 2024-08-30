import os
from cron_cleaner import startCronCleaner

# sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import load_properties
from consts import LOCAL_CONFIG_FILE
from app import app

config = load_properties(LOCAL_CONFIG_FILE)

stdJava = config['JAVA_HOME']['1.8']
if not stdJava:
    stdJava = config['JAVA_HOME'][0]
os.environ['JAVA_HOME'] = stdJava
os.environ['PATH'] = f"{config['JAVA_HOME']}\\bin;" + os.environ['PATH']
os.environ['ANDROID_SDK_ROOT'] = config['ANDROID_SDK_ROOT']
# To support gradle wrapper v3
os.environ['ANDROID_HOME'] = config['ANDROID_SDK_ROOT']

startCronCleaner()
app.run(host="0.0.0.0", port=config['NEXUS_PORT'])