# utils.py
import json
import os

def load_input(path):
    # aceita caminho relativo ou absoluto
    path = os.path.abspath(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
