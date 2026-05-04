"""
Prometheus instrumentation for LogSentinel.

Metrics exposed at /metrics (scraped by Prometheus, visualised in Grafana):
  logsentinel_logs_ingested_total        — counter, labelled by kafka topic
  logsentinel_anomalies_detected_total   — counter, labelled by severity
  logsentinel_query_latency_seconds      — histogram (p50 / p95 / p99)
  logsentinel_kafka_consumer_lag         — gauge
  logsentinel_embedding_duration_seconds — histogram
"""

from prometheus_client import Counter, Gauge, Histogram

LOGS_INGESTED = Counter(
    "logsentinel_logs_ingested_total",
    "Total log lines consumed from Kafka",
    ["topic"],
)

ANOMALIES_DETECTED = Counter(
    "logsentinel_anomalies_detected_total",
    "Total anomalous log lines flagged",
    ["severity"],   # low / medium / high
)

QUERY_LATENCY = Histogram(
    "logsentinel_query_latency_seconds",
    "End-to-end REST API query latency",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1.0],
)

EMBEDDING_DURATION = Histogram(
    "logsentinel_embedding_duration_seconds",
    "SBERT batch encoding duration",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
)

KAFKA_CONSUMER_LAG = Gauge(
    "logsentinel_kafka_consumer_lag",
    "Estimated Kafka consumer lag (messages behind latest offset)",
)
