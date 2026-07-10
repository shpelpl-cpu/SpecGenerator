from __future__ import annotations

import json
from pathlib import Path

from utils import normalize_text


class DescriptionMapper:

    def __init__(self, mapping_file: str | Path = "mappings.json"):

        self.mapping_file = Path(mapping_file)

        if not self.mapping_file.exists():
            raise FileNotFoundError(self.mapping_file)

        self.rules = []
        self.mapping = {}

        self.load()

    def load(self):

        with open(self.mapping_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.rules = data.get("rules", [])

        self.mapping = {}

        for key, value in data.get("mapping", {}).items():
            self.mapping[normalize_text(key)] = value

    def save(self):

        data = {
            "rules": self.rules,
            "mapping": dict(sorted(self.mapping.items()))
        }

        with open(self.mapping_file, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )
            f.write("\n")

    def map(self, description: str) -> str:

        text = normalize_text(description)

        # Reguły (np. każde "top")
        for rule in self.rules:
            if normalize_text(rule["contains"]) in text:
                return rule["result"]

        # Dokładne dopasowanie
        if text in self.mapping:
            return self.mapping[text]

        # Dopasowanie częściowe
        for key, value in self.mapping.items():

            if key in text:
                return value

            if text in key:
                return value

        raise ValueError(f"Nieznany opis: {description}")

    def learn(self, original: str, translated: str):

        self.mapping[normalize_text(original)] = translated

        self.save()
        self.load()
