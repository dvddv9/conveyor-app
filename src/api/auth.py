# -*- coding: utf-8 -*-
"""API-key authentication (dogfood P0 fix).

Dogfood finding: POST /analyze, /history/clear, /mode were open
to any client on 0.0.0.0:5001.

Behavior:
- If CONVEYOR_API_KEY is set in .env -> require X-API-Key header.
- If CONVEYOR_API_KEY is NOT set -> API works ONLY on 127.0.0.1
  (see main.py uvicorn.run binding).
"""
import os
from fastapi import Header, HTTPException, status

API_KEY = os.getenv("CONVEYOR_API_KEY", "").strip()


async def verify_api_key(x_api_key: str = Header(default="")) -> None:
    """FastAPI dependency: verify X-API-Key header.

    If API_KEY is empty (dev mode), allow all (main.py binds to 127.0.0.1).
    If API_KEY is set, require exact match.
    """
    if not API_KEY:
        return

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header required",
        )
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )


def is_auth_enabled() -> bool:
    """True if CONVEYOR_API_KEY is set."""
    return bool(API_KEY)