from __future__ import annotations

import json
from pathlib import Path

from utils import normalize_text


CN_DESCRIPTIONS = {
    "6107110000": "bielizna chłopięca",
    "6108210000": "bielizna damska",
    "6108220000": "bielizna damska",
    "6108920000": "szlafroki damskie",
    "6117808000": "chustki na głowę",
    "6209200090": "spodnie niemowlęce",
    "6212900000": "bielizna modelująca damska",
    "6214300090": "chustki",
    "6307909899": "wachlarze",
    "9603309000": "zestaw pędzli do makijażu",
}

PRODUCT_NAMES = {
    "rearview mirror": "samochodowe lusterko dla dzieci",
    "ensemble": "komplety",
    "dress": "sukienki",
    "skirt": "spódnice",
    "trousers": "spodnie",
    "shorts": "spodenki",
    "trousers_shorts": "spodnie, spodenki",
    "blouse": "bluzki",
    "halter top": "bluzki",
    "pajamas": "piżamy",
    "sweatshirt": "bluzy",
    "tshirts": "koszulki",
    "bodysuit": "body",
    "jumpsuit": "kombinezony",
    "vest": "kamizelki",
    "headscarf": "chustki na głowę",
    "shirt": "koszule",
    "bra": "biustonosze",
    "shapewear": "bielizna modelująca",
    "kerchief": "chustki",
    "fan": "wachlarze",
    "sandal": "sandały",
    "car sun shade umbrella": "osłony przeciwsłoneczne do samochodu",
    "anklet": "bransoletki na kostkę",
    "gardening tool": "narzędzia ogrodnicze",
    "sunglasses": "okulary przeciwsłoneczne",
    "stress-relief toy": "zabawki antystresowe",
    "balloon": "balony",
    "makeup brush set": "zestaw pędzli do makijażu",
    "hair claw": "spinki do włosów",
}

TOP_DESCRIPTIONS = {
    "camisole",
    "crop top",
    "off shoulder top",
    "tank top",
    "t shirt",
    "tube top",
}


def product_key(cn: str, description: str) -> str:

    text = normalize_text(description)

    if cn == "6104630000" and text in {"shorts", "trousers"}:
        return "trousers_shorts"

    if cn in {"6109902000", "6114300000"} and text in TOP_DESCRIPTIONS:
        return "tshirts"

    return text


def gender_bucket(gender: str) -> str:

    if gender in {"women", "girls"}:
        return "female"
    if gender in {"men", "boys"}:
        return "male"
    return gender


def _gender_suffix(genders: set[str]) -> str:

    if genders == {"women", "girls"}:
        return "damskie i dziewczęce"
    if genders == {"men", "boys"}:
        return "męskie i chłopięce"

    return {
        "women": "damskie",
        "girls": "dziewczęce",
        "men": "męskie",
        "boys": "chłopięce",
        "unisex": "uniseks",
    }.get(next(iter(genders), ""), "")


def build_description(cn: str, key: str, genders: set[str]) -> str:

    if cn in CN_DESCRIPTIONS:
        return CN_DESCRIPTIONS[cn]

    description = PRODUCT_NAMES.get(key, key)
    suffix = _gender_suffix(genders)

    return f"{description} {suffix}".strip()


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

    def map(
        self,
        description: str,
        gender: str = "",
        cn: str = "",
    ) -> str:

        text = normalize_text(description)
        key = product_key(cn, text)

        if cn in CN_DESCRIPTIONS or key in PRODUCT_NAMES:
            return build_description(cn, key, {gender} if gender else set())

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
