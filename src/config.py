import os
import yaml

def load_properties(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    print("read config")
    # print(config)
    return config