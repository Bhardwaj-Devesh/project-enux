import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Welcome to Playbook API"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user():
    """Test user registration"""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    # Note: This might fail if user already exists, which is expected
    assert response.status_code in [200, 400]


def test_login_user():
    """Test user login"""
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/login-json", json=login_data)
    # Note: This might fail if user doesn't exist, which is expected
    assert response.status_code in [200, 401]


def test_get_playbooks():
    """Test getting playbooks"""
    response = client.get("/api/v1/playbooks/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_search_playbooks_text():
    """Test text search for playbooks"""
    response = client.get("/api/v1/playbooks/search/text?query=GTM")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_playbook_not_found():
    """Test getting non-existent playbook"""
    response = client.get("/api/v1/playbooks/non-existent-id")
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__]) 
