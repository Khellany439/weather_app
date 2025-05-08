import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
import models
import auth

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    # Create tables for test database
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_user():
    # Create a test user
    db = TestingSessionLocal()
    hashed_password = auth.get_password_hash("testpassword")
    user = models.User(
        username="testuser",
        email="test@example.com",
        hashed_password=hashed_password,
        credits=10
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.close()

@pytest.fixture(scope="function")
def test_token(test_user):
    # Generate a token for the test user
    access_token = auth.create_access_token(data={"sub": test_user.username})
    return access_token

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Weather Information Cloud Service API is running"}

def test_register_user(test_db):
    response = client.post(
        "/api/users/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["credits"] == 10
    assert "password" not in data

def test_login(test_db, test_user):
    response = client.post(
        "/api/users/token",
        data={
            "username": "testuser",
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_get_current_user(test_db, test_user, test_token):
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email

def test_get_credit_balance(test_db, test_user, test_token):
    response = client.get(
        "/api/credits/balance",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert response.json() == 10

def test_protected_endpoint_without_token():
    response = client.get("/api/users/me")
    assert response.status_code == 401
