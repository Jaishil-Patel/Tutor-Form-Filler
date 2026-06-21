"""Load/save sessions and settings as local JSON files."""

from __future__ import annotations

import json
import os
from typing import List

from . import config
from .models import Session


def _ensure_dirs() -> None:
    for d in (config.DATA_DIR, config.OUTPUT_DIR, config.ASSETS_DIR):
        os.makedirs(d, exist_ok=True)


def load_sessions() -> List[Session]:
    _ensure_dirs()
    if not os.path.exists(config.SESSIONS_FILE):
        return []
    try:
        with open(config.SESSIONS_FILE, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return []
    return [Session.from_dict(d) for d in raw]


def save_sessions(sessions: List[Session]) -> None:
    _ensure_dirs()
    data = [s.to_dict() for s in sessions]
    with open(config.SESSIONS_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def load_settings() -> dict:
    _ensure_dirs()
    settings = config.default_settings()
    if os.path.exists(config.SETTINGS_FILE):
        try:
            with open(config.SETTINGS_FILE, "r", encoding="utf-8") as fh:
                stored = json.load(fh)
            # merge stored values over defaults so new keys keep their defaults
            settings.update(stored)
        except (json.JSONDecodeError, OSError):
            pass
    return settings


def save_settings(settings: dict) -> None:
    _ensure_dirs()
    with open(config.SETTINGS_FILE, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2, ensure_ascii=False)
