# -*- coding: utf-8 -*-
"""Cost tracking for LLM calls (USD per 1M tokens)."""

# Prices per 1M tokens (USD)
PRICES = {
    "deepseek-chat":     {"in": 0.14, "out": 0.28},
    "deepseek-reasoner": {"in": 0.55, "out": 2.19},
    "qwen2.5:7b":        {"in": 0.0,  "out": 0.0},
    "qwen2.5:3b":        {"in": 0.0,  "out": 0.0},
    "qwen2.5:1.5b":      {"in": 0.0,  "out": 0.0},
    "deepseek-r1:7b":    {"in": 0.0,  "out": 0.0},
    "default":           {"in": 0.0,  "out": 0.0},
}


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Returns cost in USD (rounded to 6 decimals)."""
    p = PRICES.get(model, PRICES["default"])
    cost = (tokens_in * p["in"] + tokens_out * p["out"]) / 1_000_000
    return round(cost, 6)


def sum_stage_costs(stages: list) -> float:
    """Sum cost_usd from stages _meta. Skips None."""
    total = 0.0
    for s in stages:
        if not isinstance(s, dict):
            continue
        meta = s.get("_meta", {})
        total += meta.get("cost_usd", 0.0)
    return round(total, 6)
