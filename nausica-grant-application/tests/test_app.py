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

def test_about(client):
    """Test the about route."""
    response = client.get("/about")
    assert response.status_code == 200, "Expected status code 200, but got {response.status_code}"
    assert b"about.html" in response.data, "About page content not found in response"

def test_apply(client):
    """Test the apply route."""
    response = client.get("/apply")
    assert response.status_code == 200, "Expected status code 200, but got {response.status_code}"
    assert b"application.html" in response.data, "Application page content not found in response"

def test_listview_unauthorized(client):
    """Test the listview route without being logged in."""
    response = client.get("/listview")
    assert response.status_code == 302  # Redirect to login
    assert "/admin/login" in response.location  # Ensure it redirects to the login page

def test_admin_login_get(client):
    """Test the admin login route with a GET request."""
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert b"admin_login.html" in response.data  # Ensure the admin login page template is rendered

def test_admin_login_post_missing_credentials(client):
    """Test the admin login route with missing credentials."""
    response = client.post("/admin/login", data={})
    assert response.status_code == 400
    assert b"Missing credentials!" in response.data

def test_admin_login_post_invalid_credentials(client):
    """Test the admin login route with invalid credentials."""
    data = {
        "access_key": "invalid_access",
        "secret_key": "invalid_secret"
    }
    response = client.post("/admin/login", data=data)
    assert response.status_code == 401
    assert b"Invalid credentials!" in response.data

def test_bad_request_handler(client):
    """Test the 400 error handler."""
    response = client.post("/nonexistent", data={})
    assert response.status_code == 404
    assert b"Bad Request" in response.data

def test_listview_authorized(client, mock_db):
    """Test the listview route with a logged-in user."""
    with client.session_transaction() as session:
        session["user_arn"] = "arn:aws:iam::123456789012:user/test-user"
    response = client.get("/listview")
    assert response.status_code == 200, "Expected status code 200, but got {response.status_code}"
    assert b"listview.html" in response.data, "Listview page content not found in response"

@pytest.mark.usefixtures("mock_aws_credentials")
def test_admin_login_success(mock_boto_client, mock_auth, client):
    """Test successful IAM login."""
    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {"Arn": "arn:aws:iam::123456789012:user/test-user"}
    mock_boto_client.return_value = mock_sts

    response = client.post("/admin/login", data={
        "access_key": "fake_access",
        "secret_key": "fake_secret"
    }, follow_redirects=True)

    assert response.status_code == 401, "Expected status code 401 for invalid credentials"
    assert session.get("user_arn") == "arn:aws:iam::123456789012:user/test-user", "Session user ARN not set correctly"

def test_logout(client):
    """Ensure logout clears session data."""
    with client.session_transaction() as sess:
        sess["user_arn"] = "arn:aws:iam::123456789012:user/test-user"

    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200, "Expected status code 200 after logout"
    assert "user_arn" not in session, "Session data not cleared after logout"