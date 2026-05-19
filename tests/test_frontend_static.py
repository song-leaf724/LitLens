from fastapi.testclient import TestClient

from app.main import app


def test_frontend_workspace_is_served() -> None:
    with TestClient(app) as client:
        response = client.get("/app/")

    assert response.status_code == 200
    assert "LitLens 阅读工作台" in response.text
    assert "/app/app.js" in response.text


def test_frontend_assets_are_served() -> None:
    with TestClient(app) as client:
        js_response = client.get("/app/app.js")
        css_response = client.get("/app/styles.css")

    assert js_response.status_code == 200
    assert "runAgent" in js_response.text
    assert css_response.status_code == 200
    assert ".shell" in css_response.text
