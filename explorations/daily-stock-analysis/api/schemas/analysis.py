"""Pydantic request/response schemas."""
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., description="Ticker, e.g. AAPL or SAP.DE")
    region: str | None = Field(None, description="US or EU; auto-detected if omitted")


class AnalysisSummary(BaseModel):
    run_id: str
    symbol: str
    region: str | None
    signal: str | None
    confidence: str | None
    action: str | None
    core_conclusion: str | None
    created_at: str


class AnalyzeResponse(BaseModel):
    run_id: str
    symbol: str
    region: str
    report: dict
    gaps: dict
    alert_triggers: list = []


class StockSearchResult(BaseModel):
    symbol: str
    name: str
    region: str
