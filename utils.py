from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
import re


def normalize_text(text: str) -> str:
    """
    Ujednolica tekst do porównań.
    """

    if text is None:
        return ""

    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)

    return text


def contains_word(text: str, word: str) -> bool:
    """
    Sprawdza czy tekst zawiera dane słowo.
    """

    text = normalize_text(text)
    word = normalize_text(word)

    return word in text


def to_decimal(value) -> Decimal:
    """
    Zamienia wartość z Excela na Decimal.
    """

    if value is None:
        return Decimal("0")

    if isinstance(value, Decimal):
        return value

    text = str(value).strip()

    if text == "":
        return Decimal("0")

    text = text.replace(" ", "")
    text = text.replace(",", ".")

    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0")


def clean_cn(value) -> str:
    """
    Czyści kod CN.
    """

    if value is None:
        return ""

    text = str(value).strip()

    text = text.replace(" ", "")
    text = text.replace(".0", "")

    return text


def is_valid_cn(value: str) -> bool:
    """
    Sprawdza czy wygląda jak kod CN.
    """

    value = clean_cn(value)

    return bool(re.fullmatch(r"\d{8}|\d{10}", value))


def ensure_directory(path: Path) -> None:
    """
    Tworzy katalog jeśli nie istnieje.
    """

    path.mkdir(parents=True, exist_ok=True)