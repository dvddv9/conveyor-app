# -*- coding: utf-8 -*-
"""
Хранилище историй анализов Conveyor.
"""
import json
from datetime import datetime

from src.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "history.json"


def load_history() -> list:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[Conveyor] Ошибка чтения истории: {e}")
        return []


def save_history(history: list) -> None:
    try:
        HISTORY_FILE.parent.mkdir(exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Conveyor] Ошибка сохранения истории: {e}")


def add_entry(entry: dict) -> dict:
    history = load_history()
    entry["timestamp"] = datetime.now().isoformat()
    history.append(entry)
    save_history(history)
    return entry


def clear_history() -> None:
    save_history([])
