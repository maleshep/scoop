"""Portfolio router — holdings CRUD."""
from fastapi import APIRouter, HTTPException

from api.db import PortfolioRepository

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/holdings")
def list_holdings() -> list[dict]:
    return PortfolioRepository().list_holdings()


@router.post("/holdings")
def add_holding(body: dict) -> dict:
    for k in ("symbol", "shares", "cost_basis"):
        if k not in body:
            raise HTTPException(400, f"missing {k}")
    symbol = body["symbol"]
    region = body.get("region") or ("EU" if symbol.upper().endswith((".DE", ".L", ".PA", ".AS")) else "US")
    return PortfolioRepository().add_holding(symbol, region, float(body["shares"]), float(body["cost_basis"]))


@router.delete("/holdings/{hid}")
def delete_holding(hid: int) -> dict:
    PortfolioRepository().delete_holding(hid)
    return {"deleted": hid}
