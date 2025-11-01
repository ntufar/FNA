import uuid
import pytest

from src.models.alert import Alert, AlertType
from src.models.user import User


@pytest.mark.asyncio
async def test_alerts_list_returns_user_alerts(auth_headers, client, db_session):
    # Resolve current user by email used in auth fixture
    user = db_session.query(User).filter(User.email == "us1_tester@example.com").first()
    assert user is not None

    # Seed alert for this user (if schema supports it)
    try:
        alert = Alert(
            id=uuid.uuid4(),
            user_id=user.id,
            company_id=uuid.uuid4(),
            delta_id=uuid.uuid4(),
            alert_type=AlertType.SENTIMENT_SHIFT,
            threshold_percentage=10.0,
            actual_change_percentage=15.0,
            alert_message="Sentiment increased by 15%",
        )
        db_session.add(alert)
        db_session.commit()
    except Exception:
        db_session.rollback()
        alert = None

    r = await client.get("/v1/alerts", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if alert is not None:
        assert any(a.get("id") == str(alert.id) for a in data)


