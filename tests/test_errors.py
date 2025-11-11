from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_item():
    # используем большой ID который гарантированно не существует
    # (999 был мало после nfr тестов lol)
    r = client.get("/items/999999")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body and body["error"]["code"] == "not_found"


def test_validation_error():
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "validation_error"
