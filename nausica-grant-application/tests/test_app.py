import pytest
from application import application as flask_app
from unittest.mock import patch, MagicMock
from flask import session
from application import db
from models import ApplicationForm
import uuid

@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    with flask_app.test_client() as client:
        yield client

@pytest.fixture
def mock_aws_credentials():
    """Mock AWS credentials for testing."""
    patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'fake_access_key',
        'AWS_SECRET_ACCESS_KEY': 'fake_secret_key',
        'AWS_SESSION_TOKEN': 'fake_session_token'
    }).start()
    yield
    patch.stopall()

@pytest.fixture
def mock_boto_client():
    """Mock the boto3 client."""
    mock_client = MagicMock()
    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {
        "Arn": "arn:aws:iam::123456789012:user/test-user"
    }
    mock_client.return_value = mock_sts
    yield mock_client

@pytest.fixture
def mock_auth():
    """Mock authentication function."""
    mock_auth = MagicMock()
    mock_auth.return_value = True
    yield mock_auth

@pytest.fixture
def mock_db():
    """Mock the database session."""
    with patch('application.db.session') as mock_session:
        yield mock_session

def test_home_get(client):
    """Test the home route with a GET request."""
    response = client.get("/")
    assert response.status_code == 200, "Expected status code 200, but got {response.status_code}"
    assert b"Grant Application System" in response.data, "Home page content not found in response"

def test_home_post(client, mock_db):
    """Test the home route with a POST request."""
    unique_email = f"test-{uuid.uuid4()}@example.com"
    data = {
        "first_name": "pa",
        "last_name": "fa",
        "email": unique_email,
        "grant_type": "Travel"
    }
    response = client.post("/", data=data)
    assert response.status_code == 200, "Expected status code 200, but got {response.status_code}"
    assert b"Form data has been saved successfully" in response.data, "Form submission failed"

def test_listview_unauthorized(client):
    """Test the listview route without being logged in."""
    response = client.get("/listview")
    assert response.status_code == 302  # Redirect to login
    assert "/admin/login" in response.location  # Ensure it redirects to the login page


def test_admin_login_post_missing_credentials(client):
    """Test the admin login route with missing credentials."""
    response = client.post("/admin/login", data={})
    assert response.status_code == 400
    assert b"Missing credentials!" in response.data
