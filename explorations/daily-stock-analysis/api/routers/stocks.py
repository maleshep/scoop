"""Stocks router — search + watchlist."""
from fastapi import APIRouter

import config
from api.schemas import StockSearchResult

router = APIRouter(prefix="/stocks", tags=["stocks"])

_EU_SUFFIXES = (".DE", ".L", ".PA", ".AS", ".MI", ".MC", ".SW")


def _region(symbol: str) -> str:
    return "EU" if symbol.upper().endswith(_EU_SUFFIXES) else "US"


@router.get("/search", response_model=list[StockSearchResult])
def search(q: str) -> list[dict]:
    q = q.strip().upper()
    if not q:
        return []
    out = []
    for region, spec in config.WATCHLIST.items():
        for sym in spec["tickers"] + [spec["index"]]:
            if q in sym.upper():
                out.append({"symbol": sym, "name": sym, "region": region})
    # Accept any uppercase ticker the user types verbatim.
    if not any(o["symbol"] == q for o in out) and q.replace(".", "").isalpha():
        out.append({"symbol": q, "name": q, "region": _region(q)})
    return out[:10]
