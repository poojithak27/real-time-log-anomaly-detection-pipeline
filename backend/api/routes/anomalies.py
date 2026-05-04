"""
GET /api/v1/anomalies  — paginated anomaly query with sub-200ms BM25 search.
GET /api/v1/anomalies/{id} — single anomaly detail.
"""

import time
import logging
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from core.elasticsearch_client import es
from core.config import settings
from core.metrics import QUERY_LATENCY

logger = logging.getLogger(__name__)
router = APIRouter()


class AnomalyOut(BaseModel):
    id: str
    timestamp: str
    severity: str
    anomaly_score: float
    message: str
    service: str
    alerted: bool


@router.get("/anomalies", response_model=dict)
async def list_anomalies(
    severity: Optional[str] = Query(None, description="Filter by severity: low/medium/high"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    q: Optional[str] = Query(None, description="Full-text search on message"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    t0 = time.perf_counter()

    must_clauses = []
    if severity:
        must_clauses.append({"term": {"severity": severity}})
    if service:
        must_clauses.append({"term": {"service": service}})
    if q:
        must_clauses.append({"match": {"message": q}})

    query = {"query": {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}}
    query["sort"] = [{"timestamp": {"order": "desc"}}]
    query["from"] = (page - 1) * page_size
    query["size"] = page_size

    resp = await es.search(index=settings.ES_ANOMALY_INDEX, body=query)

    QUERY_LATENCY.observe(time.perf_counter() - t0)

    hits = resp["hits"]["hits"]
    total = resp["hits"]["total"]["value"]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": [
            AnomalyOut(id=h["_id"], **h["_source"]).model_dump()
            for h in hits
        ],
    }


@router.get("/anomalies/{anomaly_id}", response_model=AnomalyOut)
async def get_anomaly(anomaly_id: str):
    t0 = time.perf_counter()
    try:
        resp = await es.get(index=settings.ES_ANOMALY_INDEX, id=anomaly_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    finally:
        QUERY_LATENCY.observe(time.perf_counter() - t0)

    return AnomalyOut(id=resp["_id"], **resp["_source"])
