"""
Unit + integration tests for LogSentinel.
Run: pytest tests/ -v
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Anomaly service ────────────────────────────────────────────────────────────

class TestSeverityMapping:
    """Test the distance → severity mapping function."""

    def test_normal_below_threshold(self):
        from services.anomaly_service import _severity
        assert _severity(0.50) == "normal"
        assert _severity(0.74) == "normal"

    def test_low_severity(self):
        from services.anomaly_service import _severity
        assert _severity(0.75) == "low"
        assert _severity(0.84) == "low"

    def test_medium_severity(self):
        from services.anomaly_service import _severity
        assert _severity(0.85) == "medium"
        assert _severity(0.91) == "medium"

    def test_high_severity(self):
        from services.anomaly_service import _severity
        assert _severity(0.92) == "high"
        assert _severity(1.00) == "high"


# ── Kafka consumer ─────────────────────────────────────────────────────────────

class TestKafkaMessageProcessing:
    """Test _process_message handles edge cases gracefully."""

    @pytest.mark.asyncio
    async def test_malformed_json_is_skipped(self):
        from services.kafka_consumer import _process_message
        # Should not raise — just log and return
        await _process_message(b"not valid json {{{{")

    @pytest.mark.asyncio
    async def test_empty_message_field_is_skipped(self):
        from services.kafka_consumer import _process_message
        payload = json.dumps({"timestamp": "2025-01-01T00:00:00Z", "level": "INFO", "service": "svc", "message": ""})
        await _process_message(payload.encode())

    @pytest.mark.asyncio
    async def test_valid_message_indexes_to_es(self):
        payload = json.dumps({
            "timestamp": "2025-01-01T00:00:00Z",
            "level": "ERROR",
            "service": "payment-service",
            "message": "Connection refused: db-primary:5432",
        }).encode()

        with patch("services.kafka_consumer.score_log", new_callable=AsyncMock) as mock_score, \
             patch("services.kafka_consumer.es") as mock_es, \
             patch("services.kafka_consumer.dispatch_alerts_if_needed", new_callable=AsyncMock):

            mock_score.return_value = (0.9, "high", [0.1] * 384)
            mock_es.index = AsyncMock(return_value={"_id": "abc123"})

            from services.kafka_consumer import _process_message
            await _process_message(payload)

            assert mock_es.index.call_count == 2   # once for log, once for anomaly


# ── API routes ─────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    with patch("core.elasticsearch_client.init_elasticsearch", new_callable=AsyncMock), \
         patch("services.kafka_consumer.start_kafka_consumer", new_callable=AsyncMock):
        from main import app
        with TestClient(app) as c:
            yield c


class TestHealthEndpoints:
    def test_liveness(self, client):
        resp = client.get("/api/v1/health/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
