import json

def load_perfume_base(path="GA_perfume_base.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
