from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_create_hero():
    response = client.post(
        "/users/",
        json={"name": "Test Hero", "age": 30, "secret_name": "Secret"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Hero"
    assert data["age"] == 30
    assert data["secret_name"] == "Secret"
    assert "id" in data