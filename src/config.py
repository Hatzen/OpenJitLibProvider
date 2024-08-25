import os
import configparser

def load_properties(file_path):
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), '..', file_path)) 

    print(config.items)

    # Convert the loaded properties into a dictionary
    properties = {}
    print("Reading properties")
    for section in config.sections():
        for key, value in config.items(section):
            print(key.upper() + "=" + value)
            properties[key.upper()] = value
            
    return properties