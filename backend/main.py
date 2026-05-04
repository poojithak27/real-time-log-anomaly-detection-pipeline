"""LogSentinel — FastAPI entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from api.routes import alerts, anomalies, health, metrics_api
from core.config import settings
from core.elasticsearch_client import init_elasticsearch
from services.kafka_consumer import start_kafka_consumer

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising Elasticsearch indices...")
    await init_elasticsearch()
    logger.info("Starting Kafka consumer...")
    task = asyncio.create_task(start_kafka_consumer())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="LogSentinel",
    description="Real-time log anomaly detection — Kafka · SBERT · Elasticsearch · Prometheus",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus scrape endpoint
app.mount("/metrics", make_asgi_app())

app.include_router(health.router,      prefix="/api/v1", tags=["health"])
app.include_router(anomalies.router,   prefix="/api/v1", tags=["anomalies"])
app.include_router(alerts.router,      prefix="/api/v1", tags=["alerts"])
app.include_router(metrics_api.router, prefix="/api/v1", tags=["metrics"])
