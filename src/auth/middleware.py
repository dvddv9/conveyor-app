# -*- coding: utf-8 -*-
"""FastAPI auth dependencies: resolve the current Clerk user (v6.1, tenant-aware v6.3)."""
import os

from fastapi import Header, HTTPException

from src.api.job_store import DEFAULT_TENANT
from src.auth.clerk import AuthError, verify_jwt

#: Fallback tenant for requests that authenticate with an API key, not Clerk.
_FALLBACK_TENANT = os.getenv("VISHAP_DEFAULT_TENANT", DEFAULT_TENANT)


def _claims_to_identity(claims: dict) -> dict:
    """Map Clerk claims to the tenant-scoped identity used by the API."""
    user_id = claims["sub"]
    return {
        "user_id": user_id,
        # Clerk org membership wins; personal accounts fall back to the user id.
        "tenant_id": claims.get("org_id") or user_id,
        "claims": claims,
    }


async def current_user(authorization: str | None = Header(None)) -> dict:
    """Resolve the current user from a Clerk `Authorization: Bearer <jwt>` header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[7:]
    try:
        claims = verify_jwt(token)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return _claims_to_identity(claims)


async def current_tenant(authorization: str | None = Header(None)) -> str:
    """Best-effort tenant for endpoints that accept either API key or Clerk JWT.

    Unlike :func:`current_user` this never raises: endpoints such as
    ``/analyze/async`` are also reachable with a plain ``X-API-Key``, which
    carries no identity. Those requests share the default tenant.
    """
    if authorization and authorization.startswith("Bearer "):
        try:
            claims = verify_jwt(authorization[7:])
        except AuthError:
            return _FALLBACK_TENANT
        return claims.get("org_id") or claims.get("sub") or _FALLBACK_TENANT
    return _FALLBACK_TENANT
