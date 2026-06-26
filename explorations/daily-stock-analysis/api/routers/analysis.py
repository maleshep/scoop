"""Analysis router — POST /analyze, GET /history, GET /history/{run_id}."""
from fastapi import APIRouter, HTTPException

from api.schemas import AnalyzeRequest, AnalyzeResponse, AnalysisSummary
from api.services import AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> dict:
    service = AnalysisService()
    return service.analyze_stock(req.symbol, req.region)


@router.get("/history", response_model=list[AnalysisSummary])
def history(limit: int = 50, symbol: str | None = None) -> list[dict]:
    service = AnalysisService()
    return service.list_history(limit=limit, symbol=symbol)


@router.get("/history/{run_id}")
def get_run(run_id: str) -> dict:
    service = AnalysisService()
    row = service.get_run(run_id)
    if not row:
        raise HTTPException(404, "run not found")
    return row
