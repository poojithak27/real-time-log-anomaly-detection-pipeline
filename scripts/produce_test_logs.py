#!/usr/bin/env python3
"""
scripts/produce_test_logs.py

Publishes synthetic log events to Kafka for local dev/demo.
Mix of normal and anomalous messages to trigger detection.

Usage:
  python scripts/produce_test_logs.py --rate 50 --duration 60
"""

import argparse
import asyncio
import json
import random
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer

NORMAL_LOGS = [
    "User login successful for user_id=4821",
    "GET /api/v1/products 200 OK 45ms",
    "Cache hit ratio: 94.2%",
    "Scheduled job completed: nightly-report",
    "Payment processed: order_id=88271 amount=49.99",
    "Database connection pool: 12/50 active",
    "Health check passed for service: inventory",
    "S3 upload complete: reports/2025-01-01.csv",
]

ANOMALY_LOGS = [
    "FATAL: Segmentation fault in worker process PID=4201",
    "Connection pool exhausted — all 50 connections in use",
    "ERROR: Deadlock detected between transactions 7731 and 7740",
    "OOM kill: process payment-worker terminated",
    "SSL certificate expiry in 2 days for api.internal",
    "Disk usage 97% on /dev/sda1 — write throttling engaged",
    "Repeated auth failures: 500 attempts in 60s from 192.168.1.55",
    "Kafka lag spike: consumer group order-events lag=142000",
]

SERVICES = ["api-gateway", "payment-service", "inventory-service", "auth-service", "order-service"]
LEVELS = ["INFO", "WARN", "ERROR", "FATAL"]


async def produce(bootstrap_servers: str, topic: str, rate: int, duration: int):
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()
    print(f"Producing {rate} msg/s for {duration}s → topic={topic}")

    try:
        end = asyncio.get_event_loop().time() + duration
        sent = 0
        while asyncio.get_event_loop().time() < end:
            # ~15% anomaly rate
            is_anomaly = random.random() < 0.15
            pool = ANOMALY_LOGS if is_anomaly else NORMAL_LOGS

            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level":     "ERROR" if is_anomaly else random.choice(["INFO", "INFO", "WARN"]),
                "service":   random.choice(SERVICES),
                "message":   random.choice(pool),
            }
            await producer.send_and_wait(topic, event)
            sent += 1

            await asyncio.sleep(1 / rate)

        print(f"Done. Sent {sent} messages.")
    finally:
        await producer.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-servers", default="localhost:9092")
    parser.add_argument("--topic", default="application-logs")
    parser.add_argument("--rate", type=int, default=50, help="Messages per second")
    parser.add_argument("--duration", type=int, default=60, help="Run duration in seconds")
    args = parser.parse_args()

    asyncio.run(produce(args.bootstrap_servers, args.topic, args.rate, args.duration))
