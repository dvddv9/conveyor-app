# -*- coding: utf-8 -*-
"""
Асинхронные стадии pipeline Conveyor.

Полная копия stages.py, но через async_chat().
Логика (parse_json_response, retry, _meta) — идентична.
"""
from src.llm.async_client import async_chat
from src.pipeline.prompts import build_prompt
from src.pipeline.stages import parse_json_response
from src.config import MAX_TOKENS


async def async_run_stage(stage_name: str, prompt_name: str, material: str,
                          context: dict | None = None,
                          temperature: float = 0.0,
                          max_tokens: int | None = None,
                          retry_on_json_fail: bool = True) -> dict:
    if max_tokens is None:
        max_tokens = MAX_TOKENS

    system, user = build_prompt(prompt_name, material, context)

    result = await async_chat(system, user, temperature=temperature, max_tokens=max_tokens)
    parsed = parse_json_response(result["text"])

    if retry_on_json_fail and "_error" in parsed and parsed["_error"] == "JSON parse failed":
        print(f"  [!] {stage_name}: JSON parse failed, retry...")
        retry_user = (
            user
            + "\n\n## ВАЖНО\n\n"
            + "Верни только валидный JSON без Markdown, без комментариев, "
            + "без текста до или после. Только { ... }."
        )
        result = await async_chat(system, retry_user, temperature=temperature, max_tokens=max_tokens)
        parsed = parse_json_response(result["text"])

    parsed["_meta"] = {
        "stage": stage_name,
        "tokens_in": result["tokens_in"],
        "tokens_out": result["tokens_out"],
        "model": result["model"],
        "mode": result["mode"],
        "json_ok": "_error" not in parsed,
    }
    return parsed


async def async_stage0_orchestrator(material: str, filename: str) -> dict:
    return await async_run_stage(
        stage_name="stage0_orchestrator",
        prompt_name="00_orchestrator",
        material=f"# File: {filename}\n\n{material}",
        temperature=0.0,
        max_tokens=2000,
    )


async def async_stage1_scanner(material: str, context: dict) -> dict:
    return await async_run_stage(
        stage_name="stage1_scanner",
        prompt_name="01_scanner",
        material=material,
        context=context,
        temperature=0.0,
    )


async def async_stage2_analyst(material: str, context: dict) -> dict:
    return await async_run_stage(
        stage_name="stage2_analyst",
        prompt_name="02_analyst",
        material=material,
        context=context,
        temperature=0.0,
    )


async def async_stage3_researcher(material: str, context: dict) -> dict:
    return await async_run_stage(
        stage_name="stage3_researcher",
        prompt_name="03_researcher",
        material=material,
        context=context,
        temperature=0.3,
    )


async def async_stage4_synthesizer(material: str, context: dict) -> dict:
    return await async_run_stage(
        stage_name="stage4_synthesizer",
        prompt_name="04_synthesizer",
        material=material,
        context=context,
        temperature=0.0,
    )


async def async_stage5_transmitter(material: str, context: dict) -> str:
    system, user = build_prompt("05_transmitter", material, context)
    result = await async_chat(system, user, temperature=0.0, max_tokens=MAX_TOKENS)
    return result["text"]
