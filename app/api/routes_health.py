"""Health check router."""
from fastapi import APIRouter
from app.config import settings
from app.database.connection import get_db_connection

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    db_ok = False
    try:
        with get_db_connection() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            db_ok = cnt == 1000
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "reference_date": settings.REFERENCE_DATE,
        "database_connected": db_ok,
        "gnani_configured": bool(settings.GNANI_API_KEY)
    }
