"""FastAPI app factory.

Local run:
    uvicorn api.app:app --reload --port 8000
"""
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Make the engine + shared modules importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # explorations/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # daily-stock-analysis/

from api.db.sqlite import init_db
from api.routers.analysis import router as analysis_router


def create_app() -> FastAPI:
    app = FastAPI(title="Daily Stock Analysis API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(analysis_router, prefix="/api/v1")
    return app


app = create_app()
