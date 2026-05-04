"""Elasticsearch async client and index initialisation."""

import logging
from elasticsearch import AsyncElasticsearch
from core.config import settings

logger = logging.getLogger(__name__)

es: AsyncElasticsearch = AsyncElasticsearch(
    [settings.ES_HOST],
    request_timeout=settings.ES_TIMEOUT,
)

LOG_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "timestamp":  {"type": "date"},
            "level":      {"type": "keyword"},
            "service":    {"type": "keyword"},
            "message":    {"type": "text"},
            "embedding":  {"type": "dense_vector", "dims": 384},
            "is_anomaly": {"type": "boolean"},
            "anomaly_score": {"type": "float"},
        }
    }
}

ANOMALY_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "timestamp":     {"type": "date"},
            "log_id":        {"type": "keyword"},
            "severity":      {"type": "keyword"},
            "anomaly_score": {"type": "float"},
            "message":       {"type": "text"},
            "service":       {"type": "keyword"},
            "alerted":       {"type": "boolean"},
        }
    }
}


async def init_elasticsearch() -> None:
    """Create indices if they don't exist."""
    for index, mapping in [
        (settings.ES_LOG_INDEX, LOG_INDEX_MAPPING),
        (settings.ES_ANOMALY_INDEX, ANOMALY_INDEX_MAPPING),
    ]:
        exists = await es.indices.exists(index=index)
        if not exists:
            await es.indices.create(index=index, body=mapping)
            logger.info("Created Elasticsearch index: %s", index)
        else:
            logger.info("Elasticsearch index already exists: %s", index)
