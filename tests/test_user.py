from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import Base, get_db
from app.models.user import User
from app.utils.token import create_access_token
import os

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

def get_test_user_token():
    db = TestingSessionLocal()
    user = User(phone_number="+15555555557")
    db.add(user)
    db.commit()
    access_token = create_access_token(data={"sub": str(user.id)})
    return access_token

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

import io

def test_upload_id_card():
    token = get_test_user_token()
    file_content = b"test_image_content"
    response = client.post(
        "/users/me/id-card",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test_id_card.jpg", io.BytesIO(file_content), "image/jpeg")},
    )
    assert response.status_code == 200
    assert "path" in response.json()

def test_upload_selfie():
    token = get_test_user_token()
    file_content = b"test_image_content"
    response = client.post(
        "/users/me/selfie",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test_selfie.jpg", io.BytesIO(file_content), "image/jpeg")},
    )
    assert response.status_code == 200
    assert "path" in response.json()
