import pytest
from application import application as flask_app

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
     # Set a SECRET_KEY for testing
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    with flask_app.test_client() as client:
        yield client


def test_home_get(client):
    """Test the home route with a GET request."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Grant Application System" in response.data  # Ensure the home page template is rendered


def test_home_post(client):
    """Test the home route with a POST request."""
    data = {
        "first_name": "pa",
        "last_name": "fa",
        "email": "pa.doe@example.com",
        "grant_type": "Travel"
    }
    response = client.post("/", data=data)
    assert response.status_code == 200
    assert b"Form data has been saved successfully" in response.data