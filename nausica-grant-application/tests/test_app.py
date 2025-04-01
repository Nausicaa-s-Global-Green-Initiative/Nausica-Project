import pytest
from application import application as flask_app
from unittest.mock import patch, MagicMock
from flask import session
from application import db
from models import ApplicationForm
import uuid
#from application import auth_utils

# Define mock boto3 client fixture
@pytest.fixture
def mock_boto_client():
    # Mock the boto3 client
    mock_client = MagicMock()
    
    # Mock the STS client behavior
    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {
        "Arn": "arn:aws:iam::123456789012:user/test-user"
    }
    mock_client.return_value = mock_sts

    yield mock_client

# Define mock auth fixture (assuming it mocks authentication function)
@pytest.fixture
def mock_auth():
    mock_auth = MagicMock()
    mock_auth.return_value = True
    yield mock_auth

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
        # Cleanup: Remove existing entries with the same email
    #db.session.query(ApplicationForm).filter_by(email="pa.doe@example.com").delete()
    #db.session.commit()
    unique_email = f"test-{uuid.uuid4()}@example.com"  # Random unique email
    """Test the home route with a POST request."""
    data = {
        "first_name": "pa",
        "last_name": "fa",
        "email": unique_email,
        "grant_type": "Travel"
    }
    response = client.post("/", data=data)

    print("Response Status Code:", response.status_code)
    print("Response Data:", response.data.decode())  # Show HTML/JSON error message

    assert response.status_code == 200
    assert b"Form data has been saved successfully" in response.data

def test_about(client):
    """Test the about route."""
    response = client.get("/about")
    assert response.status_code == 200
    assert b"about.html" in response.data  # Ensure the about page template is rendered


def test_apply(client):
    """Test the apply route."""
    response = client.get("/apply")
    assert response.status_code == 200
    assert b"application.html" in response.data  # Ensure the application page template is rendered


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


def test_bad_request_handler(client):
    """Test the 400 error handler."""
    response = client.post("/nonexistent", data={})
    assert response.status_code == 404
    assert b"Bad Request" in response.data


def test_logout(client):
    """Test the logout route."""
    with client.session_transaction() as session:
        session["user_arn"] = "test-user-arn"
    response = client.get("/logout")
    assert response.status_code == 302  # Redirect to home
    assert response.location.endswith("/")  # Ensure it redirects to the home page

##Trying to test admin login page
#@patch("application.auth_utils.is_authorized_iam_user", return_value=True)
#@patch("boto3.client")
@pytest.mark.usefixtures("mock_boto_client", "mock_auth")
def test_admin_login_success(mock_boto_client, mock_auth, client):
    """Test successful IAM login."""
    mock_sts = MagicMock()
    mock_sts.get_caller_identity.return_value = {"Arn": "arn:aws:iam::123456789012:user/test-user"}
    mock_boto_client.return_value = mock_sts

    response = client.post("/admin/login", data={
        "access_key": "fake_access",
        "secret_key": "fake_secret"
    }, follow_redirects=True)

    print("Response Status Code:", response.status_code)
    print("Response Data:", response.data.decode())

    assert response.status_code == 401
    assert session.get("user_arn") == "arn:aws:iam::123456789012:user/test-user"

def test_logout(client):
    """Ensure logout clears session data."""
    with client.session_transaction() as sess:
        sess["user_arn"] = "arn:aws:iam::123456789012:user/test-user"

    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert "user_arn" not in session