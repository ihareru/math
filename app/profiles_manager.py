import json

# from app.paths import DATA_DIR

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_FILE = os.path.join(BASE_DIR, "data", "profiles.json")


def load_profiles():
    with open(PROFILE_FILE, encoding="utf8") as f:
        return json.load(f)

def save_profiles(profiles):
    with open(PROFILE_FILE, "w", encoding="utf8") as f:
        json.dump(profiles, f, indent=4, ensure_ascii=False)