# -*- coding: utf-8 -*-
"""FastAPI auth dependency: resolve the current Clerk user (v6.1)."""
from fastapi import Header, HTTPException

from src.auth.clerk import AuthError, verify_jwt


async def current_user(authorization: str | None = Header(None)) -> dict:
    """Resolve the current user from a Clerk `Authorization: Bearer <jwt>` header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[7:]
    try:
        claims = verify_jwt(token)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return {"user_id": claims["sub"], "claims": claims}
