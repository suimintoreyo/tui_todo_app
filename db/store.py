"""JSON ファイル読み書き・バックアップ管理。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.schedule import Schedule
from utils.backup import create_backup

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCHEDULE_FILE = DATA_DIR / "schedules.json"
CONFIG_FILE = DATA_DIR / "config.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_schedules() -> list[Schedule]:
    """schedules.json からスケジュールを読み込む。"""
    _ensure_data_dir()
    if not SCHEDULE_FILE.exists():
        return []
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Schedule.from_dict(d) for d in data.get("schedules", [])]


def save_schedules(schedules: list[Schedule]) -> None:
    """スケジュールを schedules.json に書き込む（バックアップ付き）。"""
    _ensure_data_dir()
    if SCHEDULE_FILE.exists():
        create_backup(SCHEDULE_FILE)
    payload: dict[str, Any] = {
        "schedules": [s.to_dict() for s in schedules]
    }
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_config() -> dict[str, Any]:
    """config.json を読み込む。"""
    _ensure_data_dir()
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict[str, Any]) -> None:
    """config.json を書き込む。"""
    _ensure_data_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
