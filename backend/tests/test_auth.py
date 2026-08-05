from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, utc_now, verify_password
from app.main import app
from app.models.refresh_token import RefreshToken
from app.models.user import User


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


def register(
    client: TestClient,
    *,
    email: str = "user@example.com",
    display_name: str = "Wang",
    password: str = "secure-password",
):
    return client.post(
        REGISTER_URL,
        json={"email": email, "display_name": display_name, "password": password},
    )


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_health_reports_database_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_register_succeeds_and_returns_tokens(client: TestClient) -> None:
    response = register(client)
    body = response.json()
    assert response.status_code == 201
    assert body["user"]["email"] == "user@example.com"
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900
    assert body["access_token"] and body["refresh_token"]


def test_register_normalizes_email_and_display_name(client: TestClient) -> None:
    response = register(client, email="  USER@Example.COM ", display_name="  Wang  ")
    assert response.status_code == 201
    assert response.json()["user"]["email"] == "user@example.com"
    assert response.json()["user"]["display_name"] == "Wang"


def test_duplicate_email_returns_409(client: TestClient) -> None:
    assert register(client).status_code == 201
    response = register(client, email="USER@example.com")
    assert response.status_code == 409
    assert response.json()["error"] == "email_already_registered"


def test_database_does_not_store_plaintext_password(
    client: TestClient,
    db_session: Session,
) -> None:
    password = "secure-password"
    register(client, password=password)
    user = db_session.scalar(select(User).where(User.email == "user@example.com"))
    assert user is not None
    assert user.password_hash != password
    assert password not in user.password_hash


def test_password_hash_uses_argon2(client: TestClient, db_session: Session) -> None:
    register(client)
    user = db_session.scalar(select(User).where(User.email == "user@example.com"))
    assert user is not None
    assert user.password_hash.startswith("$argon2")
    assert verify_password("secure-password", user.password_hash)


def test_correct_password_login_succeeds(client: TestClient) -> None:
    register(client)
    response = client.post(LOGIN_URL, json={"email": "USER@example.com", "password": "secure-password"})
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "user@example.com"


def test_wrong_password_returns_generic_error(client: TestClient) -> None:
    register(client)
    response = client.post(LOGIN_URL, json={"email": "user@example.com", "password": "wrong-password"})
    assert response.status_code == 401
    assert response.json() == {"error": "invalid_credentials", "message": "邮箱或密码错误"}


def test_unknown_email_returns_same_generic_error(client: TestClient) -> None:
    response = client.post(LOGIN_URL, json={"email": "missing@example.com", "password": "wrong-password"})
    assert response.status_code == 401
    assert response.json() == {"error": "invalid_credentials", "message": "邮箱或密码错误"}


def test_access_token_can_get_current_user(client: TestClient) -> None:
    body = register(client).json()
    response = client.get("/api/v1/auth/me", headers=auth_headers(body["access_token"]))
    assert response.status_code == 200
    assert response.json()["id"] == body["user"]["id"]


def test_me_without_token_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_access_token"


def test_forged_access_token_is_rejected(client: TestClient) -> None:
    token = register(client).json()["access_token"] + "forged"
    response = client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_access_token"


def test_wrong_token_type_is_rejected(client: TestClient) -> None:
    body = register(client).json()
    token, _ = create_access_token(body["user"]["id"], token_type="refresh")
    response = client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_access_token"


def test_expired_access_token_is_rejected(client: TestClient) -> None:
    body = register(client).json()
    token, _ = create_access_token(body["user"]["id"], expires_delta=timedelta(seconds=-1))
    response = client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_access_token"


def test_refresh_rotates_tokens(client: TestClient) -> None:
    original = register(client).json()
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": original["refresh_token"]})
    assert response.status_code == 200
    assert response.json()["refresh_token"] != original["refresh_token"]
    assert response.json()["access_token"] != original["access_token"]


def test_old_refresh_token_is_revoked_after_rotation(client: TestClient) -> None:
    old_token = register(client).json()["refresh_token"]
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": old_token}).status_code == 200
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": old_token})
    assert response.status_code == 401
    assert response.json()["error"] == "refresh_token_revoked"


def test_new_refresh_token_can_be_used(client: TestClient) -> None:
    old_token = register(client).json()["refresh_token"]
    first = client.post("/api/v1/auth/refresh", json={"refresh_token": old_token}).json()
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert response.status_code == 200


def test_expired_refresh_token_is_rejected(client: TestClient, db_session: Session) -> None:
    raw_token = register(client).json()["refresh_token"]
    stored = db_session.scalar(select(RefreshToken))
    assert stored is not None
    stored.expires_at = utc_now() - timedelta(seconds=1)
    db_session.commit()
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": raw_token})
    assert response.status_code == 401
    assert response.json()["error"] == "refresh_token_expired"


def test_logout_prevents_future_refresh(client: TestClient) -> None:
    token = register(client).json()["refresh_token"]
    response = client.post("/api/v1/auth/logout", json={"refresh_token": token})
    assert response.status_code == 204
    retry = client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert retry.status_code == 401
    assert retry.json()["error"] == "refresh_token_revoked"


def test_refresh_token_is_hashed_in_database(client: TestClient, db_session: Session) -> None:
    raw_token = register(client).json()["refresh_token"]
    stored = db_session.scalar(select(RefreshToken))
    assert stored is not None
    assert stored.token_hash != raw_token
    assert len(stored.token_hash) == 64
    assert raw_token not in stored.token_hash


def test_update_display_name_succeeds(client: TestClient) -> None:
    body = register(client).json()
    response = client.patch(
        "/api/v1/users/me",
        headers=auth_headers(body["access_token"]),
        json={"display_name": "  New Name  "},
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "New Name"


def test_user_can_only_update_own_profile(client: TestClient) -> None:
    first = register(client, email="first@example.com", display_name="First").json()
    second = register(client, email="second@example.com", display_name="Second").json()
    response = client.patch(
        "/api/v1/users/me",
        headers=auth_headers(first["access_token"]),
        json={"display_name": "First Updated"},
    )
    assert response.status_code == 200
    second_me = client.get("/api/v1/auth/me", headers=auth_headers(second["access_token"]))
    assert second_me.json()["display_name"] == "Second"


def test_blank_display_name_is_rejected(client: TestClient) -> None:
    body = register(client).json()
    response = client.patch(
        "/api/v1/users/me",
        headers=auth_headers(body["access_token"]),
        json={"display_name": "   "},
    )
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_inactive_user_cannot_login(client: TestClient, db_session: Session) -> None:
    register(client)
    user = db_session.scalar(select(User).where(User.email == "user@example.com"))
    assert user is not None
    user.is_active = False
    db_session.commit()
    response = client.post(LOGIN_URL, json={"email": "user@example.com", "password": "secure-password"})
    assert response.status_code == 403
    assert response.json()["error"] == "user_inactive"


def test_inactive_user_cannot_access_me(client: TestClient, db_session: Session) -> None:
    body = register(client).json()
    user = db_session.get(User, body["user"]["id"])
    assert user is not None
    user.is_active = False
    db_session.commit()
    response = client.get("/api/v1/auth/me", headers=auth_headers(body["access_token"]))
    assert response.status_code == 403
    assert response.json()["error"] == "user_inactive"


def test_concurrent_duplicate_registration_returns_201_and_409() -> None:
    barrier = Barrier(2)

    def submit_registration() -> int:
        with TestClient(app, raise_server_exceptions=False) as local_client:
            barrier.wait()
            return register(local_client, email="race@example.com").status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = sorted(executor.map(lambda _index: submit_registration(), range(2)))
    assert statuses == [201, 409]
