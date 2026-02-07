from fastapi.testclient import TestClient

from app.main import app


def test_ui_page_loads():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Portfolio Reporting Studio" in response.text
