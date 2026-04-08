from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
import redis as redis_client
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "ok"
    redis_status = "ok"

    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    try:
        r = redis_client.from_url(settings.REDIS_URL)
        r.ping()
    except Exception:
        redis_status = "error"

    return {
        "status": "ok" if db_status == "ok" and redis_status == "ok" else "degraded",
        "version": "0.1.0",
        "services": {
            "database": db_status,
            "redis": redis_status,
        },
    }