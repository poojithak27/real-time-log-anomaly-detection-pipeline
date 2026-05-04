"""
/api/v1/metrics/summary  — aggregated stats for the React dashboard.
Returns anomaly counts by severity, top offending services, and ingestion rate.
"""

from fastapi import APIRouter
from core.elasticsearch_client import es
from core.config import settings

router = APIRouter()


@router.get("/metrics/summary")
async def metrics_summary():
    # Anomaly counts by severity
    severity_agg = await es.search(
        index=settings.ES_ANOMALY_INDEX,
        body={
            "size": 0,
            "aggs": {
                "by_severity": {"terms": {"field": "severity", "size": 3}},
                "over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "hour",
                        "min_doc_count": 0,
                    }
                },
            },
        },
    )

    # Top services by anomaly count
    service_agg = await es.search(
        index=settings.ES_ANOMALY_INDEX,
        body={
            "size": 0,
            "aggs": {"top_services": {"terms": {"field": "service", "size": 5}}},
        },
    )

    # Total logs ingested
    log_count = await es.count(index=settings.ES_LOG_INDEX)

    severity_buckets = severity_agg["aggregations"]["by_severity"]["buckets"]
    over_time_buckets = severity_agg["aggregations"]["over_time"]["buckets"]
    service_buckets = service_agg["aggregations"]["top_services"]["buckets"]

    return {
        "total_logs_ingested": log_count["count"],
        "anomalies_by_severity": {b["key"]: b["doc_count"] for b in severity_buckets},
        "top_services": [{"service": b["key"], "count": b["doc_count"]} for b in service_buckets],
        "anomalies_over_time": [
            {"timestamp": b["key_as_string"], "count": b["doc_count"]}
            for b in over_time_buckets
        ],
    }
