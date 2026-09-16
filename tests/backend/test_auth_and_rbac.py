import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.core.database import Base
import backend.core.database as db_module
from backend.core.models import User, Role, Permission
from backend.core.security import bootstrap_security, hash_password, verify_password, create_access_token
from backend.config import settings

TEST_DB_URL = "sqlite:///./test_auth_rbac.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_auth_test_env():
    original_engine = db_module.engine
    original_session = db_module.SessionLocal

    db_module.engine = test_engine
    db_module.SessionLocal = TestSessionLocal

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_module.get_db] = override_get_db

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()
    try:
        bootstrap_security(db)
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    db_module.engine = original_engine
    db_module.SessionLocal = original_session
    app.dependency_overrides.clear()

    if os.path.exists("./test_auth_rbac.db"):
        try:
            os.remove("./test_auth_rbac.db")
        except PermissionError:
            pass


# ============================================================================
# 1. Password Hashing & Verification Tests
# ============================================================================

def test_password_hashing_security():
    password = "SecurePassword@2026"
    hashed = hash_password(password)
    assert hashed != password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


# ============================================================================
# 2. Authentication & Login Tests
# ============================================================================

def test_valid_admin_login():
    res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "Admin@123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "ADMIN"
    assert "ADMIN" in data["roles"]
    assert "system.admin" in data["permissions"]
    assert data["username"] == "admin"


def test_valid_viewer_login():
    res = client.post("/api/v1/auth/login", data={"username": "viewer", "password": "Viewer@123"})
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "VIEWER"
    assert "dashboard.read" in data["permissions"]
    assert "system.admin" not in data["permissions"]


def test_invalid_username_login():
    res = client.post("/api/v1/auth/login", data={"username": "non_existent_user", "password": "AnyPassword"})
    assert res.status_code == 401
    assert "Incorrect username or password" in res.json()["detail"]


def test_invalid_password_login():
    res = client.post("/api/v1/auth/login", data={"username": "viewer", "password": "WrongPassword"})
    assert res.status_code == 401
    assert "Incorrect username or password" in res.json()["detail"]


def test_account_lockout_policy():
    db = TestSessionLocal()
    # Create test user for lockout testing
    test_user = User(
        username="lockout_test",
        password_hash=hash_password("Pass123!"),
        is_active=True,
        token_version=1
    )
    db.add(test_user)
    db.commit()
    db.close()

    # Fail 5 times to trigger lockout
    for _ in range(5):
        res = client.post("/api/v1/auth/login", data={"username": "lockout_test", "password": "BadPassword"})
        assert res.status_code in [401, 423]

    # 6th attempt must be locked
    res_locked = client.post("/api/v1/auth/login", data={"username": "lockout_test", "password": "Pass123!"})
    assert res_locked.status_code == 423
    assert "temporarily locked" in res_locked.json()["detail"].lower()


def test_disabled_account_login_rejected():
    db = TestSessionLocal()
    disabled_user = User(
        username="disabled_user",
        password_hash=hash_password("Pass123!"),
        is_active=False,
        token_version=1
    )
    db.add(disabled_user)
    db.commit()
    db.close()

    res = client.post("/api/v1/auth/login", data={"username": "disabled_user", "password": "Pass123!"})
    assert res.status_code == 403
    assert "disabled" in res.json()["detail"].lower()


# ============================================================================
# 3. Token Verification & Revocation Tests
# ============================================================================

def test_token_revocation_on_version_increment():
    # Login as admin
    login_res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "Admin@123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify token works for /me
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "admin"

    # Revoke tokens by incrementing token_version in DB
    db = TestSessionLocal()
    admin_user = db.query(User).filter(User.username == "admin").first()
    admin_user.token_version += 1
    db.commit()
    db.close()

    # Verify previous token is now rejected
    me_revoked_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_revoked_res.status_code == 401
    assert "revoked" in me_revoked_res.json()["detail"].lower()


# ============================================================================
# 4. RBAC Authorization & Permission Enforcement Tests
# ============================================================================

def test_viewer_cannot_access_admin_endpoints():
    # Login as viewer
    login_res = client.post("/api/v1/auth/login", data={"username": "viewer", "password": "Viewer@123"})
    token = login_res.json()["access_token"]
    viewer_headers = {"Authorization": f"Bearer {token}"}

    # Attempt to list admin users
    res = client.get("/api/v1/admin/users", headers=viewer_headers)
    assert res.status_code == 403
    assert "Administrative privileges required" in res.json()["detail"]


def test_admin_can_access_admin_endpoints():
    # Login as admin
    login_res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "Admin@123"})
    token = login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {token}"}

    # List admin users
    res = client.get("/api/v1/admin/users", headers=admin_headers)
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 3
    usernames = [u["username"] for u in users]
    assert "admin" in usernames
    assert "viewer" in usernames
    assert "analyst" in usernames


# ============================================================================
# 5. Admin User Management CRUD & Safeguard Tests
# ============================================================================

def test_admin_user_lifecycle_crud():
    login_res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "Admin@123"})
    admin_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 1. Create new user
    new_user_payload = {
        "username": "sre_lead",
        "password": "InitialPassword@123",
        "email": "sre@opsintel.internal",
        "display_name": "SRE Lead Engineer",
        "roles": ["ANALYST"]
    }
    create_res = client.post("/api/v1/admin/users", json=new_user_payload, headers=admin_headers)
    assert create_res.status_code == 201
    user_id = create_res.json()["user_id"]

    # 2. Get user detail
    detail_res = client.get(f"/api/v1/admin/users/{user_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["username"] == "sre_lead"
    assert "ANALYST" in detail_res.json()["roles"]

    # 3. Update user
    update_res = client.put(f"/api/v1/admin/users/{user_id}", json={"display_name": "Senior SRE Lead", "roles": ["ANALYST", "VIEWER"]}, headers=admin_headers)
    assert update_res.status_code == 200

    # 4. Admin reset password
    reset_res = client.post(f"/api/v1/admin/users/{user_id}/reset-password", json={"new_password": "NewSecretPassword@2026"}, headers=admin_headers)
    assert reset_res.status_code == 200

    # 5. Verify login with new password
    sre_login_res = client.post("/api/v1/auth/login", data={"username": "sre_lead", "password": "NewSecretPassword@2026"})
    assert sre_login_res.status_code == 200
    assert "ANALYST" in sre_login_res.json()["roles"]

    # 6. Delete user
    del_res = client.delete(f"/api/v1/admin/users/{user_id}", headers=admin_headers)
    assert del_res.status_code == 200


def test_admin_cannot_disable_or_delete_last_admin():
    login_res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "Admin@123"})
    admin_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Find admin user ID
    users_res = client.get("/api/v1/admin/users", headers=admin_headers)
    admin_id = next(u["id"] for u in users_res.json() if u["username"] == "admin")

    # Attempt to disable last admin
    disable_res = client.put(f"/api/v1/admin/users/{admin_id}", json={"is_active": False}, headers=admin_headers)
    assert disable_res.status_code == 400
    assert "Cannot disable the last active administrator" in disable_res.json()["detail"]

    # Attempt to delete last admin
    delete_res = client.delete(f"/api/v1/admin/users/{admin_id}", headers=admin_headers)
    assert delete_res.status_code == 400
    assert "Cannot delete the last active administrator" in delete_res.json()["detail"]
