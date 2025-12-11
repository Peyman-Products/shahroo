import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.db import Base, get_db
from app.models.user import User
from app.models.permission import Role
from app.utils.token import create_access_token
from app.models.business import Business
from app.models.task import Task
from app.models.location import Country, Province, City
from app.models.task_meta import TaskCategory

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def cleanup_database(db_session: Session):
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def owner_role(db_session: Session):
    owner = Role(name="owner")
    db_session.add(owner)
    db_session.commit()
    db_session.refresh(owner)
    return owner

@pytest.fixture
def admin_user(db_session: Session, owner_role: Role):
    admin = User(phone_number="+15555555558", role_id=owner_role.id)
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

def get_admin_token(admin_user: User):
    return create_access_token(data={"sub": str(admin_user.id), "role": "owner"})

def test_get_users(admin_user: User):
    token = get_admin_token(admin_user)
    response = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_business(admin_user: User):
    token = get_admin_token(admin_user)
    response = client.post(
        "/admin/businesses/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Business", "phone_number": "+15555555559", "address": "123 Main St"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Business"

def test_create_task(admin_user: User, db_session: Session):
    token = get_admin_token(admin_user)

    business = Business(name="Test Business 2", phone_number="+15555555560", address="456 Oak Ave", created_by_admin_id=admin_user.id)
    country = Country(name="Test Country")
    province = Province(name="Test Province", country=country)
    city = City(name="Test City", province=province)
    category = TaskCategory(name="Test Category")
    db_session.add_all([business, country, province, city, category])
    db_session.commit()
    db_session.refresh(business)
    db_session.refresh(city)
    db_session.refresh(category)

    response = client.post(
        "/admin/tasks/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Task",
            "business_id": business.id,
            "price": 10.0,
            "estimated_time": 60,
            "start_datetime": "2025-01-01T12:00:00Z",
            "address": "789 Pine St",
            "lat": 34.0522,
            "lng": -118.2437,
            "start_location_country_id": city.province.country.id,
            "start_location_province_id": city.province.id,
            "start_location_city_id": city.id,
            "category_id": category.id,
            "steps": [{"title": "Step 1", "description": "Do something", "address": "789 Pine St", "lat": 34.0522, "lng": -118.2437, "estimated_time": 30, "order": 1}]
        }
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Test Task"

def test_approve_task(admin_user: User, db_session: Session):
    token = get_admin_token(admin_user)

    user = User(phone_number="+15555555561", verification_status="verified")
    business = Business(name="Test Business 3", phone_number="+15555555562", address="101 Maple St", created_by_admin_id=admin_user.id)
    country = Country(name="Test Country")
    province = Province(name="Test Province", country=country)
    city = City(name="Test City", province=province)
    category = TaskCategory(name="Test Category")
    db_session.add_all([user, business, country, province, city, category])
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(business)
    db_session.refresh(city)
    db_session.refresh(category)

    task_data = {
        "title": "Test Task 2",
        "business_id": business.id,
        "price": 20.0,
        "estimated_time": 120,
        "start_datetime": "2025-01-02T12:00:00Z",
        "address": "111 Pine St",
        "lat": 34.0522,
        "lng": -118.2437,
        "start_location_country_id": city.province.country.id,
        "start_location_province_id": city.province.id,
        "start_location_city_id": city.id,
        "category_id": category.id,
        "steps": [{"title": "Step 1", "description": "Do something", "address": "111 Pine St", "lat": 34.0522, "lng": -118.2437, "estimated_time": 60, "order": 1}]
    }

    response = client.post("/admin/tasks/", headers={"Authorization": f"Bearer {token}"}, json=task_data)
    assert response.status_code == 200
    task_id = response.json()["id"]

    db_task = db_session.query(Task).filter(Task.id == task_id).first()
    db_task.status = "done"
    db_task.assigned_user_id = user.id
    db_session.commit()
    db_session.refresh(db_task)

    response = client.post(f"/admin/tasks/{task_id}/approve", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
