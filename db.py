import os
import json

def load(name):
    if not os.path.exists(name):
        return None

    with open(name, "r") as f:
        return json.load(f)

def dump(obj, name):
    with open(name, "w") as f:
        json.dump(obj, f)
