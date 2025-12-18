from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import Base, get_db
from app.models.user import User, VerificationStatus
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


def test_upload_kyc_media_in_single_request_returns_urls_and_status():
    token = get_test_user_token()
    file_content = b"test_image_content"

    response = client.post(
        "/users/me/kyc/media",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "id_card": ("test_id_card.jpg", io.BytesIO(file_content), "image/jpeg"),
            "selfie": ("test_selfie.jpg", io.BytesIO(file_content), "image/jpeg"),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == VerificationStatus.pending.value
    assert data["id_card"]["url"].startswith("/media/users/")
    assert data["selfie"]["url"].startswith("/media/users/")


def test_user_me_returns_media_urls_for_unapproved_user():
    phone_number = "+19999999999"
    token, _ = create_or_get_user(
        phone_number=phone_number,
        verification_status=VerificationStatus.pending,
        id_card_image="users/sample/kyc/id-card/example-id.jpg",
        selfie_image="users/sample/kyc/selfie/example-selfie.jpg",
    )

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["phone_number"] == phone_number
    assert data["verification_status"] == VerificationStatus.pending.value
    assert data["id_card_url"] == "/media/users/sample/kyc/id-card/example-id.jpg"
    assert data["selfie_url"] == "/media/users/sample/kyc/selfie/example-selfie.jpg"


def test_get_kyc_media_returns_images_for_unapproved_user():
    phone_number = "+18888888888"
    token, _ = create_or_get_user(
        phone_number=phone_number,
        verification_status=VerificationStatus.pending,
        id_card_image="users/sample/kyc/id-card/example-id.jpg",
        selfie_image="users/sample/kyc/selfie/example-selfie.jpg",
    )

    response = client.get("/users/me/kyc/media", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == VerificationStatus.pending.value
    assert data["id_card"]["url"].endswith("example-id.jpg")
    assert data["selfie"]["url"].endswith("example-selfie.jpg")
    assert "pending review" in data["message"].lower()


def test_get_kyc_media_returns_approval_message_for_verified_user():
    phone_number = "+17777777778"
    token, _ = create_or_get_user(
        phone_number=phone_number,
        verification_status=VerificationStatus.verified,
        id_card_image="users/sample/kyc/id-card/example-id.jpg",
        selfie_image="users/sample/kyc/selfie/example-selfie.jpg",
    )

    response = client.get("/users/me/kyc/media", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == VerificationStatus.verified.value
    assert data["id_card"] is None
    assert data["selfie"] is None
    assert "approved" in data["message"].lower()


def test_get_kyc_media_returns_denied_message_with_images_for_rejected_user():
    phone_number = "+16666666667"
    token, _ = create_or_get_user(
        phone_number=phone_number,
        verification_status=VerificationStatus.rejected,
        id_card_image="users/sample/kyc/id-card/example-id.jpg",
        selfie_image="users/sample/kyc/selfie/example-selfie.jpg",
    )

    response = client.get("/users/me/kyc/media", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == VerificationStatus.rejected.value
    assert data["id_card"]["url"].endswith("example-id.jpg")
    assert data["selfie"]["url"].endswith("example-selfie.jpg")
    assert "denied" in data["message"].lower()
