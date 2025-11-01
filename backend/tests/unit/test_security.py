from src.core.security import AuthenticationManager, create_user_tokens, hash_password, verify_password


def test_password_hash_and_verify():
    pwd = "StrongP@ssw0rd!"
    hashed = hash_password(pwd)
    assert hashed and isinstance(hashed, str)
    assert verify_password(pwd, hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_create_and_verify():
    mgr = AuthenticationManager()
    user = {"id": "123", "email": "x@y.z", "subscription_tier": "Pro"}
    tokens = create_user_tokens(user)
    assert "access_token" in tokens and "refresh_token" in tokens
    payload = mgr.verify_token(tokens["access_token"])
    assert payload["email"] == user["email"]
    extracted = mgr.extract_user_from_token(tokens["access_token"])
    assert extracted["subscription_tier"] == "Pro"


