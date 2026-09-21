import os
os.environ["EMCOIN_JWT_SECRET"]="test-secret-for-suite"
os.environ["DATABASE_URL"]="sqlite:///./data/test_emcoin.db"

from fastapi.testclient import TestClient
from app.main import app, Base, engine

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
client=TestClient(app)

def test_health_and_readiness():
    assert client.get("/health").status_code==200
    assert client.get("/health/ready").json()["status"]=="ready"

def test_register_and_me():
    r=client.post("/api/v1/auth/register",json={"full_name":"Test Investor","email":"test@example.com","password":"Password123!"})
    assert r.status_code==200
    token=r.json()["access_token"]
    me=client.get("/api/v1/auth/me",headers={"Authorization":f"Bearer {token}"})
    assert me.status_code==200
    assert me.json()["customerId"].startswith("C-")

def test_protected_route_requires_auth():
    assert client.get("/api/v1/positions").status_code==401
