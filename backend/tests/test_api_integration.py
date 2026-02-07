from io import BytesIO

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.models import entities  # noqa: F401
from app.models.entities import User
from app.main import app


def _client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def _get_db_override():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db_override
    return TestClient(app), TestingSessionLocal


def test_auth_upload_and_pack_download():
    client, _ = _client()
    register = client.post(
        "/auth/register",
        params={"org_name": "Test Org", "email": "user@example.com", "password": "pass"},
    )
    assert register.status_code == 200

    login = client.post("/auth/login", params={"email": "user@example.com", "password": "pass"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    company = client.post(
        "/companies",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Acme", "sector": "SaaS"},
    )
    assert company.status_code == 200
    company_id = company.json()["id"]

    csv_data = "period,category,amount\n2024-01-01,Revenue,1000\n2024-01-01,COGS,200\n2024-01-01,Sales & Marketing,300\n2024-01-01,Cash,5000\n"
    files = {"file": ("actuals.csv", BytesIO(csv_data.encode("utf-8")), "text/csv")}
    upload = client.post(
        f"/companies/{company_id}/actuals",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert upload.status_code == 200

    pack = client.get(f"/companies/{company_id}/pack", headers={"Authorization": f"Bearer {token}"})
    assert pack.status_code == 200
    assert pack.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment; filename=company_" in pack.headers["content-disposition"]

    mapping_status = client.get(
        f"/companies/{company_id}/mappings/status", headers={"Authorization": f"Bearer {token}"}
    )
    assert mapping_status.status_code == 200
    assert mapping_status.json()["unmapped_accounts"] == []

    export = client.get(
        f"/companies/{company_id}/mappings/export", headers={"Authorization": f"Bearer {token}"}
    )
    assert export.status_code == 200
    assert "source_account,canonical_category" in export.text

    settings = client.get("/org/settings", headers={"Authorization": f"Bearer {token}"})
    assert settings.status_code == 200
    updated = client.put(
        "/org/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "runway_risk_threshold": 9.0,
            "revenue_drop_threshold": -0.2,
            "margin_drop_threshold": -0.15,
        },
    )
    assert updated.status_code == 200

    logs = client.get("/audit/logs", headers={"Authorization": f"Bearer {token}"})
    assert logs.status_code == 200


def test_viewer_cannot_create_company():
    client, session_factory = _client()
    register = client.post(
        "/auth/register",
        params={"org_name": "Test Org", "email": "viewer@example.com", "password": "pass"},
    )
    assert register.status_code == 200

    session = session_factory()
    try:
        user = session.query(User).filter(User.email == "viewer@example.com").first()
        user.role = "viewer"
        session.commit()
    finally:
        session.close()

    login = client.post("/auth/login", params={"email": "viewer@example.com", "password": "pass"})
    token = login.json()["access_token"]

    response = client.post(
        "/companies",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Blocked", "sector": "Tech"},
    )
    assert response.status_code == 403

