from datetime import datetime, timezone

from fastapi import APIRouter
from sqlmodel import Session
from sqlalchemy import text

from app.db.database import engine

router = APIRouter()


@router.get(
    "/health",
    tags=["Health"],
    summary="Application health check",
)
def health_check():
    return {
        "status": "ok",
        "service": "enterprise-ai-workspace",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/health/db",
    tags=["Health"],
    summary="Database health check",
)
def database_health():
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "detail": str(e),
        }