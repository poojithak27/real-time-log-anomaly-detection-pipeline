"""
Alert dispatch service.

Loads active alert rules from PostgreSQL.
For each anomaly, evaluates matching rules and POSTs to their webhook URLs.
Implements per-rule cooldown to suppress alert storms.
"""

import asyncio
import logging
import time
from typing import Any, Dict

import httpx
from sqlalchemy import select

from core.config import settings
from core.database import AsyncSessionLocal
from models.alert_rule import AlertRule

logger = logging.getLogger(__name__)

# In-memory cooldown tracker: rule_id → last_fired_epoch
_last_fired: Dict[int, float] = {}


async def dispatch_alerts_if_needed(anomaly_id: str, anomaly: Dict[str, Any]) -> None:
    """
    Evaluate all active alert rules against the anomaly.
    Fire webhook for any rule whose severity threshold is met and whose
    cooldown period has elapsed.
    """
    severity_rank = {"low": 1, "medium": 2, "high": 3}
    anomaly_rank = severity_rank.get(anomaly["severity"], 0)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AlertRule).where(AlertRule.active == True)
        )
        rules = result.scalars().all()

    tasks = []
    for rule in rules:
        rule_rank = severity_rank.get(rule.min_severity, 3)
        if anomaly_rank < rule_rank:
            continue  # below this rule's threshold

        now = time.time()
        last = _last_fired.get(rule.id, 0)
        if now - last < settings.ALERT_COOLDOWN_SECONDS:
            logger.debug("Suppressing alert for rule %d (cooldown)", rule.id)
            continue

        _last_fired[rule.id] = now
        tasks.append(_fire_webhook(rule, anomaly_id, anomaly))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def _fire_webhook(rule: "AlertRule", anomaly_id: str, anomaly: Dict[str, Any]) -> None:
    payload = {
        "rule_name":     rule.name,
        "anomaly_id":    anomaly_id,
        "severity":      anomaly["severity"],
        "service":       anomaly["service"],
        "message":       anomaly["message"],
        "anomaly_score": anomaly["anomaly_score"],
        "timestamp":     anomaly["timestamp"],
    }

    try:
        async with httpx.AsyncClient(timeout=settings.WEBHOOK_TIMEOUT_SECONDS) as client:
            resp = await client.post(rule.webhook_url, json=payload)
            resp.raise_for_status()
            logger.info(
                "Alert fired | rule=%s status=%d anomaly_id=%s",
                rule.name, resp.status_code, anomaly_id,
            )
    except httpx.HTTPError as exc:
        logger.error("Webhook delivery failed for rule %s: %s", rule.name, exc)
