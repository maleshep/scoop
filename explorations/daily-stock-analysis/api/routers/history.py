"""History router — browse all analysis runs (reuses AnalysisService.get_run)."""
from fastapi import APIRouter

from api.services import AnalysisService

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/")
def list_runs(limit: int = 100, symbol: str | None = None) -> list[dict]:
    return AnalysisService().list_history(limit=limit, symbol=symbol)


@router.get("/{run_id}")
def get_run(run_id: str) -> dict:
    return AnalysisService().get_run(run_id)
