"""
Kafka consumer — Extension 1 (real-time ingest pipeline).

Consumes JSON log events from the `application-logs` topic,
runs SBERT anomaly scoring on each message, indexes results
to Elasticsearch, and updates Prometheus metrics.

Expected message schema (JSON):
{
  "timestamp": "2025-01-01T00:00:00Z",
  "level":     "ERROR",
  "service":   "payment-service",
  "message":   "Connection refused: db-primary:5432"
}
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError

from core.config import settings
from core.elasticsearch_client import es
from core.metrics import KAFKA_CONSUMER_LAG, LOGS_INGESTED
from services.anomaly_service import score_log
from services.alert_service import dispatch_alerts_if_needed

logger = logging.getLogger(__name__)

RETRY_BACKOFF = [2, 5, 15, 30]   # seconds between reconnect attempts


async def _process_message(raw: bytes) -> None:
    """Decode → score → index one Kafka message."""
    try:
        event = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("Malformed Kafka message, skipping: %s", exc)
        return

    message_text = event.get("message", "")
    if not message_text:
        return

    anomaly_score, severity, embedding = await score_log(message_text)
    is_anomaly = severity != "normal"

    doc = {
        "timestamp":     event.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "level":         event.get("level", "UNKNOWN").upper(),
        "service":       event.get("service", "unknown"),
        "message":       message_text,
        "embedding":     embedding,
        "is_anomaly":    is_anomaly,
        "anomaly_score": anomaly_score,
    }

    await es.index(index=settings.ES_LOG_INDEX, document=doc)

    if is_anomaly:
        anomaly_doc = {
            "timestamp":     doc["timestamp"],
            "log_id":        None,   # populated after ES returns _id if needed
            "severity":      severity,
            "anomaly_score": anomaly_score,
            "message":       message_text,
            "service":       doc["service"],
            "alerted":       False,
        }
        resp = await es.index(index=settings.ES_ANOMALY_INDEX, document=anomaly_doc)
        await dispatch_alerts_if_needed(resp["_id"], anomaly_doc)

    LOGS_INGESTED.labels(topic=settings.KAFKA_TOPIC).inc()


async def start_kafka_consumer() -> None:
    """Long-running coroutine — reconnects on transient Kafka errors."""
    attempt = 0

    while True:
        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_GROUP_ID,
            auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
            enable_auto_commit=True,
            value_deserializer=None,   # raw bytes; we decode in _process_message
        )

        try:
            await consumer.start()
            logger.info(
                "Kafka consumer started | topic=%s group=%s",
                settings.KAFKA_TOPIC,
                settings.KAFKA_GROUP_ID,
            )
            attempt = 0   # reset backoff on successful connect

            async for msg in consumer:
                # Update consumer lag gauge (end_offset - current_offset)
                try:
                    partitions = consumer.assignment()
                    end_offsets = await consumer.end_offsets(partitions)
                    lag = sum(
                        end_offsets[p] - consumer.position(p)
                        for p in partitions
                        if end_offsets.get(p) is not None
                    )
                    KAFKA_CONSUMER_LAG.set(lag)
                except Exception:
                    pass   # non-critical; don't crash the consumer

                await _process_message(msg.value)

        except KafkaConnectionError as exc:
            backoff = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
            logger.error(
                "Kafka connection error (attempt %d), retrying in %ds: %s",
                attempt + 1, backoff, exc,
            )
            attempt += 1
            await asyncio.sleep(backoff)

        except asyncio.CancelledError:
            logger.info("Kafka consumer task cancelled — shutting down.")
            break

        finally:
            try:
                await consumer.stop()
            except Exception:
                pass
