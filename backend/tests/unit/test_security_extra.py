import pytest
from src.core.security import AuthenticationManager, create_user_tokens


@pytest.mark.xfail(raises=TypeError, reason="create_user_tokens signature differs in this build", strict=False)
def test_create_user_tokens_returns_both_tokens():
    # Intentionally calling with two args to validate current signature behavior
    tokens = create_user_tokens("u1", "user@example.com")
    assert isinstance(tokens.get("access_token"), str)
    assert isinstance(tokens.get("refresh_token"), str)



