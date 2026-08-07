import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SETTINGS_FILE = os.path.join(BASE_DIR, "data", "settings.json")

def load_settings():
    with open(SETTINGS_FILE, encoding="utf8") as f:
        return json.load(f)


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf8") as f:
        json.dump(settings, f, indent=4)



