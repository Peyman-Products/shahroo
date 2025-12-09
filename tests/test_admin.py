from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import Base, get_db
from app.models.user import User
from app.utils.token import create_access_token
from app.models.business import Business
from app.models.task import Task

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

def get_admin_token():
    db = TestingSessionLocal()
    admin = User(phone_number="+15555555558", role="admin")
    db.add(admin)
    db.commit()
    access_token = create_access_token(data={"sub": str(admin.id), "role": admin.role})
    return access_token

def test_get_users():
    token = get_admin_token()
    response = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_business():
    token = get_admin_token()
    response = client.post("/admin/businesses", headers={"Authorization": f"Bearer {token}"}, json={"name": "Test Business", "contact_person": "John Doe", "phone_number": "+15555555559", "address": "123 Main St"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test Business"

def test_create_task():
    token = get_admin_token()
    db = TestingSessionLocal()
    business = Business(name="Test Business 2", contact_person="Jane Doe", phone_number="+15555555560", address="456 Oak Ave")
    db.add(business)
    db.commit()
    response = client.post("/admin/tasks", headers={"Authorization": f"Bearer {token}"}, json={"title": "Test Task", "business_id": business.id, "price": 10.0, "estimated_time": 60, "start_datetime": "2025-01-01T12:00:00Z", "start_address": "789 Pine St", "start_lat": 34.0522, "start_lng": -118.2437, "start_country_id": 1, "start_province_id": 1, "start_city_id": 1, "category_id": 1, "steps": [{"title": "Step 1", "description": "Do something", "address": "789 Pine St", "lat": 34.0522, "lng": -118.2437, "estimated_time": 30, "order": 1}]})
    assert response.status_code == 200
    assert response.json()["title"] == "Test Task"

def test_approve_task():
    token = get_admin_token()
    db = TestingSessionLocal()
    user = User(phone_number="+15555555561", verification_status="verified")
    business = Business(name="Test Business 3", contact_person="Jim Doe", phone_number="+15555555562", address="101 Maple St")
    task = Task(title="Test Task 2", business_id=business.id, price=20.0, estimated_time=120, start_datetime="2025-01-02T12:00:00Z", status="done", assigned_user_id=user.id)
    db.add_all([user, business, task])
    db.commit()
    response = client.post(f"/admin/tasks/{task.id}/approve", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
