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


def build_prompt(
    name: str,
    material: str,
    context: dict | None = None,
    web_search_results: list | None = None,
) -> tuple[str, str]:
    """
    Возвращает (system, user) для LLM.

    Args:
        name: имя промпта (00_orchestrator, 02_analyst, ...)
        material: анализируемый материал
        context: контекст (stage0, stage1, ...)
        web_search_results: результаты Tavily (список dict с results)
    """
    system = load_prompt(name)

    parts = [f"## MATERIAL\n\n{material}"]

    if context:
        parts.append(
            f"## CONTEXT\n\n```json\n{json.dumps(context, ensure_ascii=False, indent=2)}\n```"
        )

    if web_search_results:
        search_block = _format_search_results(web_search_results)
        parts.append(
            "## Web Search Results (real-time)\n\n"
            "The following search results were retrieved to provide up-to-date context.\n"
            "Use them to identify recent CVEs, patches, and best practices.\n"
            "Cite them in your analysis where relevant.\n\n"
            f"{search_block}"
        )

    user = "\n\n".join(parts)
    return system, user


def _format_search_results(web_search_results: list) -> str:
    """Форматирует результаты Tavily в компактный markdown."""
    lines = []
    for i, search in enumerate(web_search_results, 1):
        query = search.get("query", "?")
        results = search.get("results", [])
        lines.append(f"### Query {i}: {query}")
        if not results:
            lines.append("(no results)")
            continue
        for j, item in enumerate(results, 1):
            title = item.get("title", "?")
            url = item.get("url", "?")
            content = item.get("content", "")
            snippet = content[:500].replace("\n", " ")
            lines.append(f"{j}. **{title}** — {url}")
            if snippet:
                lines.append(f"   {snippet}")
        lines.append("")
    return "\n".join(lines)
