"""Webhook handler endpoints for FNA API.

Provides endpoints for enterprise users to configure webhooks and receive
notifications for analysis completion, alerts, and batch processing events.
"""

import uuid
import hmac
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel, validator, HttpUrl
from sqlalchemy.orm import Session

from ...core.security import require_enterprise_tier
from ...core.api_auth import get_current_user_or_api_key
from ...database.connection import get_db
from ...models.user import User

router = APIRouter()


class WebhookConfig(BaseModel):
    """Webhook configuration model."""
    url: HttpUrl
    events: List[str]  # e.g., ["analysis.completed", "alert.triggered", "batch.completed"]
    secret: Optional[str] = None  # Secret for signature validation
    
    @validator('events')
    def validate_events(cls, v):
        allowed_events = [
            "analysis.completed",
            "analysis.failed",
            "alert.triggered",
            "batch.completed",
            "batch.failed",
            "report.uploaded"
        ]
        for event in v:
            if event not in allowed_events:
                raise ValueError(f"Invalid event: {event}. Allowed: {allowed_events}")
        return v


class WebhookResponse(BaseModel):
    """Webhook configuration response."""
    id: str
    url: str
    events: List[str]
    is_active: bool
    created_at: str


class WebhookDelivery(BaseModel):
    """Webhook delivery record."""
    id: str
    webhook_id: str
    event_type: str
    status: str  # "pending", "delivered", "failed"
    attempts: int
    delivered_at: Optional[str]
    error_message: Optional[str]


async def deliver_webhook(
    webhook_url: str,
    payload: Dict[str, Any],
    secret: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """
    Deliver webhook payload to configured URL.
    
    Args:
        webhook_url: Target webhook URL
        payload: Payload data to send
        secret: Optional secret for signature generation
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Generate signature if secret provided
        headers = {"Content-Type": "application/json"}
        if secret:
            payload_json = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                secret.encode('utf-8'),
                payload_json.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            headers["X-FNA-Signature"] = f"sha256={signature}"
        
        # Send webhook
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=headers
            )
            
            if response.status_code < 400:
                return True, None
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
                
    except Exception as e:
        return False, str(e)


@router.post("/", response_model=WebhookResponse)
async def create_webhook(
    webhook_config: WebhookConfig,
    current_user: Dict[str, Any] = Depends(require_enterprise_tier),
    db: Session = Depends(get_db)
):
    """Create a new webhook configuration.
    
    Requires Enterprise subscription.
    """
    user = db.query(User).filter(User.id == uuid.UUID(current_user["id"])).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # In a real implementation, store webhook config in database
    # For now, return a mock response
    webhook_id = str(uuid.uuid4())
    
    return WebhookResponse(
        id=webhook_id,
        url=str(webhook_config.url),
        events=webhook_config.events,
        is_active=True,
        created_at=datetime.now(timezone.utc).isoformat()
    )


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    current_user: Dict[str, Any] = Depends(require_enterprise_tier),
    db: Session = Depends(get_db)
):
    """List all webhook configurations for the current user.
    
    Requires Enterprise subscription.
    """
    # In a real implementation, query webhook configs from database
    return []


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    current_user: Dict[str, Any] = Depends(require_enterprise_tier),
    db: Session = Depends(get_db)
):
    """Send a test webhook to verify configuration.
    
    Requires Enterprise subscription.
    """
    # In a real implementation, fetch webhook config and send test payload
    test_payload = {
        "event": "webhook.test",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "message": "This is a test webhook from FNA"
        }
    }
    
    # For now, just return success
    return {
        "success": True,
        "message": "Test webhook would be sent to configured URL"
    }


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: Dict[str, Any] = Depends(require_enterprise_tier),
    db: Session = Depends(get_db)
):
    """Delete a webhook configuration.
    
    Requires Enterprise subscription.
    """
    # In a real implementation, delete webhook config from database
    return {"success": True, "message": "Webhook deleted"}

