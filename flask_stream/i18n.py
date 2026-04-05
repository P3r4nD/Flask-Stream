import json
import os


def load_translations(lang):

    base = os.path.dirname(__file__)
    path = os.path.join(base, "i18n", f"{lang}.json")

    if not os.path.exists(path):
        path = os.path.join(base, "i18n", "en.json")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
