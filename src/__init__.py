import os
from cron_cleaner import startCronCleaner

# sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import load_properties
from app import app

config = load_properties("config.yml")

os.environ['JAVA_HOME'] = config['JAVA_HOME']
os.environ['PATH'] = f"{config['JAVA_HOME']}\\bin;" + os.environ['PATH']
os.environ['ANDROID_SDK_ROOT'] = config['ANDROID_SDK_ROOT']
# To support gradle wrapper v3
os.environ['ANDROID_HOME'] = config['ANDROID_SDK_ROOT']

startCronCleaner()
app.run(host="0.0.0.0", port=config['NEXUS_PORT'])