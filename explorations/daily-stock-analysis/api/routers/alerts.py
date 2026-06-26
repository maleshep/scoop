"""Alerts router — rule CRUD + trigger history."""
from fastapi import APIRouter, HTTPException

from api.db import AlertRepository

router = APIRouter(prefix="/alerts", tags=["alerts"])

RULE_TYPES = ["rsi_above", "rsi_below", "price_above", "price_below", "signal_change"]


@router.get("/rules")
def list_rules(active: bool = False) -> list[dict]:
    return AlertRepository().list_rules(active_only=active)


@router.post("/rules")
def add_rule(body: dict) -> dict:
    if body.get("rule_type") not in RULE_TYPES:
        raise HTTPException(400, f"rule_type must be one of {RULE_TYPES}")
    return AlertRepository().add_rule(body["symbol"], body["rule_type"], float(body["threshold"]))


@router.patch("/rules/{aid}")
def toggle_rule(aid: int, body: dict) -> dict:
    AlertRepository().toggle_rule(aid, bool(body.get("active", True)))
    return {"id": aid, "active": body.get("active")}


@router.delete("/rules/{aid}")
def delete_rule(aid: int) -> dict:
    AlertRepository().delete_rule(aid)
    return {"deleted": aid}


@router.get("/events")
def list_events(limit: int = 50) -> list[dict]:
    return AlertRepository().list_events(limit)
