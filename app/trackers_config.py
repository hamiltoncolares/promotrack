from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml

DEFAULT_TRACKERS_CONTENT = {"trackers": []}


class TrackersConfigStore:
    def __init__(self, path: Path):
        self.path = path

    def ensure_file(self) -> None:
        if self.path.exists():
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(DEFAULT_TRACKERS_CONTENT, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def load(self) -> list[dict[str, Any]]:
        self.ensure_file()
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        trackers = raw.get("trackers", [])
        if not isinstance(trackers, list):
            raise ValueError("Arquivo config/trackers.yaml invalido: 'trackers' deve ser lista")
        return trackers

    def save(self, trackers: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"trackers": trackers}
        self.path.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )


def tracker_entry_to_dict(
    tracker_id: str,
    wine_name: str,
    site: str,
    start_date: date,
    end_date: date,
    active: bool = True,
) -> dict[str, Any]:
    return {
        "id": tracker_id,
        "wine_name": wine_name,
        "site": site,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "active": active,
    }


def parse_entry_dates(entry: dict[str, Any]) -> tuple[date, date]:
    start_raw = entry.get("start_date")
    end_raw = entry.get("end_date")
    if not start_raw or not end_raw:
        raise ValueError(f"Tracker invalido (id={entry.get('id')}): start_date/end_date obrigatorios")
    start_date = date.fromisoformat(str(start_raw))
    end_date = date.fromisoformat(str(end_raw))
    if end_date < start_date:
        raise ValueError(f"Tracker invalido (id={entry.get('id')}): end_date < start_date")
    return start_date, end_date
