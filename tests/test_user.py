from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import Base, get_db
from app.models.user import User
from app.utils.token import create_access_token
import os

if os.path.exists("test.db"):
    os.remove("test.db")

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

def create_or_get_user(phone_number="+15555555557", **kwargs):
    db = TestingSessionLocal()
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        user = User(phone_number=phone_number, **kwargs)
        db.add(user)
    else:
        for attr, value in kwargs.items():
            setattr(user, attr, value)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(data={"sub": str(user.id)})
    db.close()
    return access_token, user

def get_test_user_token(phone_number="+15555555557", **kwargs):
    token, _ = create_or_get_user(phone_number, **kwargs)
    return token

def test_get_user_me():
    token = get_test_user_token()
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["phone_number"] == "+15555555557"

def test_update_user_me():
    token = get_test_user_token()
    response = client.patch("/users/me", headers={"Authorization": f"Bearer {token}"}, json={"first_name": "John", "last_name": "Doe"})
    assert response.status_code == 200
    assert response.json()["first_name"] == "John"
    assert response.json()["last_name"] == "Doe"

def test_update_user_me_duplicate_shaba_number():
    existing_shaba = "IR123456789123456789123456"
    _, existing_user = create_or_get_user(phone_number="+16666666666", shaba_number=existing_shaba)
    token = get_test_user_token(phone_number="+17777777777")

    response = client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"shaba_number": existing_user.shaba_number},
    )

    assert response.status_code == 400
    assert "Shaba number" in response.json()["detail"]

import io

def test_upload_id_card():
    token = get_test_user_token()
    file_content = b"test_image_content"
    response = client.post(
        "/users/me/kyc/id-card",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test_id_card.jpg", io.BytesIO(file_content), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "uploaded"
    assert "upload_id" in response.json()

def test_upload_selfie():
    token = get_test_user_token()
    file_content = b"test_image_content"
    response = client.post(
        "/users/me/kyc/selfie",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test_selfie.jpg", io.BytesIO(file_content), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "uploaded"
    assert "upload_id" in response.json()
