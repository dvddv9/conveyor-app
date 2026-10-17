# -*- coding: utf-8 -*-
"""
Хранилище историй анализов Vishap.
"""
import json
import threading
from datetime import datetime

from src.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "history.json"

# Thread lock for safe concurrent writes (batch mode)
_HISTORY_LOCK = threading.Lock()


def load_history() -> list:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[Vishap] Ошибка чтения истории: {e}")
        return []


def save_history(history: list) -> None:
    try:
        HISTORY_FILE.parent.mkdir(exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Vishap] Ошибка сохранения истории: {e}")


def add_entry(entry: dict) -> dict:
    with _HISTORY_LOCK:
        history = load_history()
        entry["timestamp"] = datetime.now().isoformat()
        history.append(entry)
        save_history(history)
        return entry


def clear_history() -> None:
    with _HISTORY_LOCK:
        save_history([])


def find_done_by_hash(material_hash: str) -> dict | None:
    """Возвращает последнюю завершённую запись с таким material_hash, или None.

    Завершённая = есть verdict (pipeline дошёл до audit).
    """
    if not material_hash:
        return None
    history = load_history()
    # Идём с конца — последняя запись приоритетнее
    for entry in reversed(history):
        if entry.get("material_hash") == material_hash and entry.get("verdict"):
            return entry
    return None
