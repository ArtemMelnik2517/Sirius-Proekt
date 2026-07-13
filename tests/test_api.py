import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, engine
import os

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup():
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    init_db()
    yield

def test_signup_and_token():
    r = client.post("/users/signup", params={"username":"testuser","password":"pass"})
    assert r.status_code == 201
    r2 = client.post("/token", data={"username":"testuser","password":"pass"})
    assert r2.status_code == 200
    assert "access_token" in r2.json()

def test_spaces_and_reservation_conflict():
    client.post("/users/signup", params={"username":"tmpadmin","password":"apass"})
    r = client.post("/token", data={"username":"admin","password":"adminpass"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    rs = client.post("/spaces", json={"name":"Hall1","capacity":10,"equipment":["proj"]}, headers=headers)
    assert rs.status_code == 201
    space_id = rs.json()["id"]
    client.post("/users/signup", params={"username":"u1","password":"p"})
    ruser = client.post("/token", data={"username":"u1","password":"p"})
    tok_user = ruser.json()["access_token"]
    h = {"Authorization": f"Bearer {tok_user}"}
    r1 = client.post("/reservations", json={
        "space_id": space_id,
        "start_at": "2030-01-01T10:00:00+00:00",
        "end_at":   "2030-01-01T11:00:00+00:00",
        "user_name": "u1"
    }, headers=h)
    assert r1.status_code == 201
    r2 = client.post("/reservations", json={
        "space_id": space_id,
        "start_at": "2030-01-01T10:30:00+00:00",
        "end_at":   "2030-01-01T11:30:00+00:00",
        "user_name": "u1"
    }, headers=h)
    assert r2.status_code == 409
