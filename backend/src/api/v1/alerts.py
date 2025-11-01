"""Alerts endpoints for managing user alerts."""

from __future__ import annotations

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...core.security import get_current_user
from ...database.connection import get_db
from ...models.alert import Alert


router = APIRouter()


class AlertResponse(BaseModel):
    id: str
    alert_type: str
    message: str
    severity: str
    is_read: bool


@router.get("/", response_model=List[AlertResponse])
@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Alert).filter(Alert.user_id == current_user["id"]).order_by(Alert.created_at.desc())
    alerts = query.offset(skip).limit(limit).all()
    return [
        AlertResponse(
            id=str(a.id),
            alert_type=a.alert_type.value if a.alert_type else "",
            message=a.alert_message,
            severity=a.severity_level,
            is_read=a.is_read,
        )
        for a in alerts
    ]


