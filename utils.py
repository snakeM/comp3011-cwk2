import json


def load_json(path):
    with open(path, "r") as file:
        data = json.load(file)
        return data
