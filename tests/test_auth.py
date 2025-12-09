from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import Base, get_db
from app.models.otp import OTP
from datetime import datetime, timedelta, timezone

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_send_otp():
    response = client.post("/auth/send-otp", json={"phone_number": "+15555555555"})
    assert response.status_code == 200
    assert response.json() == {"message": "OTP sent successfully"}

def test_verify_otp():
    db = TestingSessionLocal()
    otp_code = "123456"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=2)
    db_otp = OTP(phone_number="+15555555555", otp_code=otp_code, expires_at=expires_at)
    db.add(db_otp)
    db.commit()

    response = client.post("/auth/verify-otp", json={"phone_number": "+15555555555", "otp_code": "123456"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_verify_otp_invalid():
    response = client.post("/auth/verify-otp", json={"phone_number": "+15555555555", "otp_code": "654321"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid or expired OTP"}

def test_otp_rate_limit():
    for _ in range(3):
        client.post("/auth/send-otp", json={"phone_number": "+15555555556"})
    response = client.post("/auth/send-otp", json={"phone_number": "+15555555556"})
    assert response.status_code == 429
    assert response.json() == {"detail": "Too many OTP requests. Please try again later."}
