import os
import json

def read_config(config_path: str) -> dict: # TODO put this in a utils file
    if os.path.exists(config_path):     
        with open(config_path, "r") as file:
            return json.load(file)
    else:
        return {}