"""System config router — watchlist + model provider (runtime, in-memory).

For the local PoC the watchlist is mutated on the loaded config object
(not persisted to disk); restart resets it. A future iteration can write
to a config file. Provider toggle sets config.MODEL_PROVIDER + resets the
cached analyzer provider.
"""
from fastapi import APIRouter

import config
import analyzer

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/config")
def get_config() -> dict:
    return {
        "model_provider": config.MODEL_PROVIDER,
        "glm_model": config.GLM_MODEL,
        "watchlist": config.WATCHLIST,
        "anthropic_configured": bool(config.ANTHROPIC_API_KEY or config.ANTHROPIC_AUTH_TOKEN),
        "glm_configured": True,
        "email_enabled": config.email_enabled(),
    }


@router.put("/config")
def put_config(body: dict) -> dict:
    if "model_provider" in body:
        provider = body["model_provider"].lower()
        if provider not in ("glm", "claude"):
            return {"error": "provider must be glm or claude"}
        config.MODEL_PROVIDER = provider
        # reset the cached provider so the next call uses the new one
        analyzer._PROVIDER = None
    if "watchlist" in body:
        wl = body["watchlist"]
        if isinstance(wl, dict):
            config.WATCHLIST = wl
    return get_config()
