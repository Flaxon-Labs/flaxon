import pytest

from flaxon import Flaxon
from flaxon.admin.services import AdminAuth
from flaxon.exceptions import Forbidden
from flaxon.security import JWTBackend, SessionBackend, User, authenticate, login_required
from flaxon.testing import TestClient


@pytest.fixture
def jwt_backend():
    return JWTBackend(secret_key="test-secret-key")


@pytest.fixture
def session_backend():
    return SessionBackend()


def test_jwt_authentication():
    app = Flaxon("test-auth")

    backend = JWTBackend(secret_key="test-secret")

    @app.post("/login")
    async def login(request):
        data = await request.json()
        user = User(id=1, username=data.get("username"), email=data.get("email"))
        token = await backend.create_token(user)
        return {"token": token}

    @app.get("/protected")
    @login_required
    async def protected(request):
        user = getattr(request, "user", None)
        return {"user": user.to_dict() if user else None}

    client = TestClient(app)

    response = client.post("/login", json_data={"username": "alice", "email": "alice@example.com"})
    assert response.status_code == 200
    token = response.json()["token"]

    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    result = response.json()
    assert result["user"]["username"] == "alice"


def test_jwt_invalid_token():
    app = Flaxon("test-auth")

    backend = JWTBackend(secret_key="test-secret")

    @app.get("/protected")
    @login_required
    async def protected(request):
        return {"ok": True}

    client = TestClient(app)

    response = client.get("/protected", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401


def test_jwt_expired_token():
    import asyncio

    app = Flaxon("test-auth")

    backend = JWTBackend(secret_key="test-secret")

    @app.get("/protected")
    @login_required
    async def protected(request):
        return {"ok": True}

    user = User(id=1, username="alice")
    token = asyncio.run(backend.create_token(user, expires_in=1))

    asyncio.run(asyncio.sleep(2))

    client = TestClient(app)
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_session_authentication():
    app = Flaxon("test-session-auth")

    backend = SessionBackend()

    @app.post("/login")
    async def login(request):
        data = await request.json()
        user = User(id=1, username=data.get("username"))
        session_id = await backend.create_token(user)
        return {"session_id": session_id}

    @app.get("/protected")
    @login_required
    async def protected(request):
        user = getattr(request, "user", None)
        return {"user": user.to_dict() if user else None}

    client = TestClient(app)

    response = client.post("/login", json_data={"username": "bob"})
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    response = client.get("/protected", headers={"Authorization": f"Bearer {session_id}"})
    assert response.status_code == 200
    result = response.json()
    assert result["user"]["username"] == "bob"


def test_session_expired():
    app = Flaxon("test-session-expired")

    backend = SessionBackend()

    @app.post("/login")
    async def login(request):
        data = await request.json()
        user = User(id=1, username=data.get("username"))
        session_id = await backend.create_token(user, expires_in=1)
        return {"session_id": session_id}

    @app.get("/protected")
    @login_required
    async def protected(request):
        return {"ok": True}

    client = TestClient(app)

    response = client.post("/login", json_data={"username": "charlie"})
    session_id = response.json()["session_id"]

    import time
    time.sleep(2)

    response = client.get("/protected", headers={"Authorization": f"Bearer {session_id}"})
    assert response.status_code == 401


def test_admin_password_reset_tokens_expire_and_change_password():
    auth = AdminAuth([{"username": "alice", "email": "alice@example.com", "password": "OldSecret123!"}])
    token = auth.request_password_reset("alice@example.com")
    assert token
    assert auth.reset_password(token, "NewSecret123!") is True
    assert auth.verify("alice", "NewSecret123!") is not None
    assert auth.reset_password(token, "AnotherSecret123!") is False


def test_admin_email_verification_tokens_are_single_use():
    auth = AdminAuth([{"username": "alice", "email": "alice@example.com", "password": "Secret123!"}])
    token = auth.request_email_verification("alice")
    assert token
    assert auth.verify_email(token) is True
    assert auth.verify_email(token) is False
    assert auth.users["alice"]["email_verified"] is True


def test_admin_role_permissions_are_enforced():
    auth = AdminAuth([{"username": "editor", "password": "Secret123!", "roles": ["editor"], "permissions": []}])
    auth.role_permissions = {"editor": ["product:read"]}
    auth.authorize(auth.user("editor"), "product:read")
    with pytest.raises(Forbidden):
        auth.authorize(auth.user("editor"), "product:delete")
