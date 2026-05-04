"""
Anomaly detection service.

Strategy:
  1. Encode incoming log message with SBERT (all-MiniLM-L6-v2, 384-dim).
  2. Query Elasticsearch k-NN to find the k closest known-normal embeddings.
  3. Compute mean cosine distance to those neighbours.
  4. Flag as anomaly if distance > settings.ANOMALY_THRESHOLD.

Severity mapping:
  distance < 0.75   → normal
  0.75 – 0.85       → low
  0.85 – 0.92       → medium
  > 0.92            → high
"""

import logging
import time
from typing import Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

from core.config import settings
from core.elasticsearch_client import es
from core.metrics import ANOMALY_DETECTED, EMBEDDING_DURATION

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading SBERT model: %s", settings.SBERT_MODEL)
        _model = SentenceTransformer(settings.SBERT_MODEL)
    return _model


def _severity(score: float) -> str:
    if score < 0.75:
        return "normal"
    if score < 0.85:
        return "low"
    if score < 0.92:
        return "medium"
    return "high"


async def score_log(message: str) -> Tuple[float, str, list]:
    """
    Returns (anomaly_score, severity, embedding_list).
    anomaly_score is mean cosine distance to k nearest normal neighbours.
    """
    model = get_model()

    t0 = time.perf_counter()
    embedding: np.ndarray = model.encode(message, normalize_embeddings=True)
    EMBEDDING_DURATION.observe(time.perf_counter() - t0)

    # kNN search against known-normal log embeddings
    knn_query = {
        "knn": {
            "field": "embedding",
            "query_vector": embedding.tolist(),
            "k": 10,
            "num_candidates": 50,
            "filter": {"term": {"is_anomaly": False}},
        },
        "_source": ["anomaly_score"],
    }

    resp = await es.search(index=settings.ES_LOG_INDEX, body=knn_query)
    hits = resp["hits"]["hits"]

    if not hits:
        # No baseline yet — treat as anomaly with max distance
        anomaly_score = 1.0
    else:
        # Use ES _score (dot-product of normalised vectors = cosine similarity)
        # Convert similarity → distance
        similarities = [h["_score"] for h in hits]
        anomaly_score = float(1.0 - np.mean(similarities))

    severity = _severity(anomaly_score)

    if severity != "normal":
        ANOMALY_DETECTED.labels(severity=severity).inc()

    return anomaly_score, severity, embedding.tolist()
