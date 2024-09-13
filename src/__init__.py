import os
import sys
from cron_cleaner import startCronCleaner

# sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import load_properties
from consts import LOCAL_CONFIG_FILE
from app import app

config = load_properties(LOCAL_CONFIG_FILE)
print(config)

stdJava = None
try:
    stdJava = config['JAVA_HOME']['1.8']
except:
    print("No java 1.8 version found, leading to errors building old gradlewrapper")
if not stdJava:
    stdJava = list(config['JAVA_HOME'].values())[0]


os.environ['JAVA_HOME'] = stdJava
os.environ['PATH'] = f"{stdJava}\\bin;" + os.environ['PATH']
os.environ['ANDROID_SDK_ROOT'] = config['ANDROID_SDK_ROOT']
# To support gradle wrapper v3
os.environ['ANDROID_HOME'] = config['ANDROID_SDK_ROOT']

startCronCleaner()
# TODO: Remove or at least make debugApp.py
app.run(host="0.0.0.0", port=config['NEXUS_PORT'])