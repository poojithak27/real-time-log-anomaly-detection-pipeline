"""Health and readiness endpoints."""

from fastapi import APIRouter
from core.elasticsearch_client import es

router = APIRouter()


@router.get("/health/live")
async def liveness():
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness():
    try:
        info = await es.cluster.health()
        es_status = info.get("status", "unknown")
    except Exception as exc:
        return {"status": "degraded", "elasticsearch": str(exc)}, 503
    return {"status": "ok", "elasticsearch": es_status}
