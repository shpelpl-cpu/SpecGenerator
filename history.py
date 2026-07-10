from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import shutil


class GenerationHistory:

    def __init__(self, history_file: str | Path = "history/history.json"):

        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.load()

    def load(self) -> list[dict]:

        try:
            with self.history_file.open("r", encoding="utf-8") as file:
                entries = json.load(file)

            if not self._entries_are_valid(entries):
                raise ValueError("Historia musi być listą wpisów.")

            return entries

        except FileNotFoundError:
            self._save([])
            return []

        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            self._backup_broken_file()
            self._save([])
            return []

    def add(
        self,
        invoice: str,
        output: str,
        positions: int,
        groups: int,
        value: float,
    ):

        entries = self.load()
        entries.append(
            {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "invoice": invoice,
                "output": output,
                "positions": positions,
                "groups": groups,
                "value": value,
            }
        )
        self._save(entries)

    def delete(self, index: int):

        entries = self.load()
        del entries[index]
        self._save(entries)

    def _save(self, entries: list[dict]):

        with self.history_file.open("w", encoding="utf-8") as file:
            json.dump(entries, file, ensure_ascii=False, indent=2)
            file.write("\n")

    def _backup_broken_file(self):

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.history_file.with_name(
            f"history_broken_{timestamp}.json"
        )
        shutil.copy2(self.history_file, backup_file)

    @staticmethod
    def _entries_are_valid(entries: object) -> bool:

        required_fields = {"date", "invoice", "output", "positions", "groups", "value"}

        return (
            isinstance(entries, list)
            and all(
                isinstance(entry, dict)
                and required_fields.issubset(entry)
                and isinstance(entry["value"], (int, float))
                for entry in entries
            )
        )
