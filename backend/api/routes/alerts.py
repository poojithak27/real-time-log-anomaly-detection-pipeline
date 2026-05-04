"""
CRUD endpoints for alert rules.

POST   /api/v1/alerts/rules        — create rule
GET    /api/v1/alerts/rules        — list rules
PATCH  /api/v1/alerts/rules/{id}   — update rule
DELETE /api/v1/alerts/rules/{id}   — delete rule
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.alert_rule import AlertRule

router = APIRouter()


class RuleIn(BaseModel):
    name: str
    webhook_url: HttpUrl
    min_severity: str = "high"
    service_filter: str | None = None
    active: bool = True


class RuleOut(BaseModel):
    id: int
    name: str
    webhook_url: str
    min_severity: str
    service_filter: str | None
    active: bool


@router.post("/alerts/rules", response_model=RuleOut, status_code=201)
async def create_rule(payload: RuleIn, db: AsyncSession = Depends(get_db)):
    rule = AlertRule(**payload.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/alerts/rules", response_model=list[RuleOut])
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertRule))
    return result.scalars().all()


@router.patch("/alerts/rules/{rule_id}", response_model=RuleOut)
async def update_rule(rule_id: int, payload: RuleIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/alerts/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(AlertRule).where(AlertRule.id == rule_id))
    await db.commit()
