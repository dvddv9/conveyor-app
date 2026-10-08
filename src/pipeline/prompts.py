# -*- coding: utf-8 -*-
"""
Загрузка промптов V5.7.
"""
import json
from functools import lru_cache
from pathlib import Path

from src.config import PROMPTS_DIR


@lru_cache(maxsize=16)
def load_prompt(name: str) -> str:
    """Загружает промпт по имени (00_orchestrator → 00_orchestrator.md)."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Промпт не найден: {path}")
    return path.read_text(encoding="utf-8")


def build_prompt(name: str, material: str, context: dict | None = None) -> tuple[str, str]:
    """Возвращает (system, user) для LLM."""
    system = load_prompt(name)
    if context:
        user = (
            f"## MATERIAL\n\n{material}\n\n"
            f"## CONTEXT\n\n```json\n{json.dumps(context, ensure_ascii=False, indent=2)}\n```"
        )
    else:
        user = f"## MATERIAL\n\n{material}"
    return system, user
