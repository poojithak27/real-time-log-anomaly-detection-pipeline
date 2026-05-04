"""Central configuration — all values come from environment variables."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Elasticsearch
    ES_HOST: str = "http://elasticsearch:9200"
    ES_LOG_INDEX: str = "logs"
    ES_ANOMALY_INDEX: str = "anomalies"
    ES_TIMEOUT: int = 30

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_TOPIC: str = "application-logs"
    KAFKA_GROUP_ID: str = "logsentinel-consumer"
    KAFKA_AUTO_OFFSET_RESET: str = "latest"

    # ML
    SBERT_MODEL: str = "all-MiniLM-L6-v2"      # lightweight; swap for larger if GPU available
    ANOMALY_THRESHOLD: float = 0.75             # cosine distance threshold for anomaly flag
    EMBEDDING_BATCH_SIZE: int = 64

    # Alert Webhooks
    WEBHOOK_TIMEOUT_SECONDS: int = 5
    ALERT_COOLDOWN_SECONDS: int = 60            # suppress repeated alerts for same rule

    # PostgreSQL (alert rules store)
    DATABASE_URL: str = "postgresql+asyncpg://logsentinel:secret@postgres:5432/logsentinel"

    # Prometheus
    METRICS_ENABLED: bool = True

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
