"""Basic Flask application for rendering web pages."""

import os, boto3
import time
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate
from flasgger import Swagger, swag_from
from flask_login import login_required
from db_config import db  # Import db from db_config
from models import ApplicationForm 
from flask_wtf.csrf import CSRFProtect

 
application = Flask(__name__)
application.secret_key = os.getenv("FLASK_SECRET_KEY")
swagger = Swagger(application)


# Load environment variables from .env file
load_dotenv()


# Create and initialize CSRF protection
csrf = CSRFProtect(application)

#-----------------------------------------

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(application)
login_manager.login_view = "admin_login"  # Redirects unauthorized users to login page

# User class for authentication
class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

#----------------------------------------------------


# HTTPS Redirect Middleware
@application.before_request
def before_request():
    # Don't redirect HTTPS requests (prevents redirect loops)
    if request.is_secure:
        pass
    # Skip HTTPS redirect for localhost
    elif 'localhost' in request.host or '127.0.0.1' in request.host:
        pass
    # Redirect HTTP to HTTPS in production
    else:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)
    
    # Configure cookies based on environment
    if 'localhost' in request.host or '127.0.0.1' in request.host:
        application.config['SESSION_COOKIE_SECURE'] = False
        application.config['REMEMBER_COOKIE_SECURE'] = False
        application.config['SESSION_COOKIE_DOMAIN'] = None
    else:
        application.config['SESSION_COOKIE_SECURE'] = True
        application.config['REMEMBER_COOKIE_SECURE'] = True

# Set up database configuration
application.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 3306)}/{os.getenv('DB_NAME')}"
)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(application)  # Initialize db with app

# Initialize Flask Migrate
migrate = Migrate(application, db)

@application.route("/", methods=['GET', 'POST'])
def home():
    """Handle POST requests for form submissions."""
    if request.method == 'POST':
        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            grant_type = request.form['grant_type']

            # Create an instance of GrantApplication model with the form submission data
            application_form = ApplicationForm(
                first_name=first_name,
                last_name=last_name,
                email=email,
                grant_type=grant_type
            )

            # Add the new form data to the database session
            db.session.add(application_form)

            # Commit the session to save data to the database
            db.session.commit()
            return jsonify(message="Form data has been saved successfully"), 200
        except SQLAlchemyError as e:
            # Handle exceptions from the try block
            db.session.rollback()
            return jsonify(error=str(e), message="Failed to process request"), 500

    # Render the home page using the 'home.html' template for GET requests and for any other non-POST method.
    return render_template("home.html")

@application.errorhandler(400)
def handle_bad_request(e):
    """Handle 400 Bad Request errors."""
    print("Failed to process request:", request.form)
    return "Bad Request: Check terminal for more details.", 400

@application.route("/about")
def about():
    """Render the about page using the 'about.html' template."""
    return render_template("about.html")

@application.route('/apply')
def apply():
    """Render the application.html page."""
    session['visited_apply'] = True
    #print("Session contents:", dict(session))  # Debug session
    #print("Secret key is set:", application.secret_key is not None)  # Check if key is loaded
    return render_template('application.html')

### Swagger: Get for all grant applications
@application.route('/listview')
@login_required
@swag_from({
    'summary': 'List all applications',
    'description': 'Displays all submitted applications in tabular format',
    'responses': {
        '200': {
            'description': 'List of applications displayed successfully'
        }
    }
})


def listview():
    """Retrieve all records and display in an HTML page using SQLAlchemy."""
    try:
        records = ApplicationForm.query.all()
    except SQLAlchemyError as e:
        print("Error fetching data:", str(e))
        records = []

    return render_template('listview.html', records=records)




#----------------------

# Flask-Login setup

ALLOWED_IAM_GROUP = "Flask-Admin"  # Group name to restrict access

class User(UserMixin):
    def __init__(self, username):
        self.id = username

def is_authorized_iam_user(arn):
    """
    Checks if the IAM user belongs to the Flask-Admin group.
    """
    iam_client = boto3.client('iam')
    user_name = arn.split("/")[-1]  # Extract IAM username from ARN

    try:
        # Check if the user belongs to the allowed IAM group
        groups = iam_client.list_groups_for_user(UserName=user_name)
        for group in groups.get('Groups', []):
            if group['GroupName'] == ALLOWED_IAM_GROUP:
                print(f"User {user_name} is in the allowed group: {ALLOWED_IAM_GROUP}")
                return True  # User is authorized immediately when found

        print(f"User {user_name} is NOT in the allowed group: {ALLOWED_IAM_GROUP}")
    
    except boto3.exceptions.Boto3Error as boto_error:
        print(f"IAM API error: {boto_error}")
    except Exception as e:
        print(f"Authorization check failed for {user_name}: {e}")

    return False  # Deny access if not in the allowed group

@application.route('/admin/login', methods=['GET'])
def admin_login_get():
    """Render the admin login page for GET requests."""
    return render_template('admin_login.html')


@application.route('/admin/login', methods=['POST'])
def admin_login():
    """Authenticate IAM Users & Check Authorization"""
    if request.method == 'POST':
        access_key = request.form.get('access_key')
        secret_key = request.form.get('secret_key')

        if not access_key or not secret_key:
            return "Missing credentials!", 400

        try:
            # Authenticate IAM User
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )

            identity = sts_client.get_caller_identity()
            user_arn = identity["Arn"]  # IAM User ARN
            user_id = identity["UserId"]

            print(f"Successfully authenticated: {user_arn} (User ID: {user_id})")

            # Check if user is authorized (belongs to the allowed IAM group)
            if not is_authorized_iam_user(user_arn):
                print(f"Access Denied for {user_arn}")
                return "Access Denied: Unauthorized IAM User", 403

            # Allow access & log in user
            login_user(User(user_arn))
            session['user_arn'] = user_arn  # Store only the ARN, not credentials

            return redirect(url_for('listview'))

        except boto3.exceptions.Boto3Error as boto_error:
            print(f"Authentication failed due to AWS API error: {boto_error}")
            return "Authentication failed: AWS API error", 500
        except Exception as e:
            print(f"Authentication failed: {e}")
            return "Authentication failed: Invalid AWS credentials", 401

    return render_template('admin_login.html')


@application.route('/admin')
@login_required
def admin_dashboard():
    return f"Welcome to the Admin Panel! Logged in as: {session.get('user_arn')}."


@application.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop("user_arn", None)  # Remove user data from session

    return redirect(url_for('home'))

#----------------------


@application.route('/edit/<int:id>', methods=['GET'])
@login_required
def edit_application(id):
    """Display the form for editing an application."""
    try:
        # Fetch record by ID using SQLAlchemy
        record = db.session.get(ApplicationForm, id)
        if not record:
            return "Record not found", 404
    except SQLAlchemyError as e:
        print("Error fetching data:", str(e))
        return "Database error", 500

    return render_template('edit_form.html', record=record)

@application.route('/edit/<int:id>', methods=['POST'])
def update_application(id):
    """Process the form submission to update an application."""
    try:
        # Fetch record by ID using SQLAlchemy
        record = db.session.get(ApplicationForm, id)
        if not record:
            return "Record not found", 404

        # **Double-check if the record still exists before updating**
        db.session.refresh(record)  # Ensures the record is not deleted

        if not record:
            return "Error: Record was deleted before updating.", 404

        # Get updated form data
        record.first_name = request.form.get('first-name', record.first_name)
        record.last_name = request.form.get('last-name', record.last_name)
        record.email = request.form.get('email', record.email)
        record.grant_type = request.form.get('grant-type', record.grant_type)

        # Handle numeric fields safely
        try:
            record.funding_amount = float(request.form.get('funding-amount', record.funding_amount))
        except ValueError:
            return "Invalid funding amount", 400

        record.special_award = request.form.get('special-award-checkbox') == "on"
        record.award_details = request.form.get('special-award-details', record.award_details)

        # Commit changes to the database
        db.session.commit()
        print(f"Record {id} updated successfully!")
    except SQLAlchemyError as e:
        db.session.rollback()
        print("Error updating data:", str(e))
        return "Failed to update record", 500

    return redirect(url_for('listview'))  # Redirect to the list after updating


### Swagger: POST for application form
@application.route('/submit', methods=['POST'])
@swag_from({
    'summary': 'Submit a new grant application',
    'description': 'Accepts form data for a new grant application and saves it to the database',
    'parameters': [
        {
            'name': 'first-name',
            'in': 'formData',
            'type': 'string',
            'required': True
        },
        {
            'name': 'last-name',
            'in': 'formData',
            'type': 'string',
            'required': True
        },
        {
            'name': 'email',
            'in': 'formData',
            'type': 'string',
            'required': True
        },
        {
            'name': 'grant-type',
            'in': 'formData',
            'type': 'string',
            'required': True
        },
        {
            'name': 'funding-amount',
            'in': 'formData',
            'type': 'number',
            'format': 'float',
            'required': True
        },
        {
            'name': 'special-award-checkbox',
            'in': 'formData',
            'type': 'string',
            'required': False
        },
        {
            'name': 'special-award-details',
            'in': 'formData',
            'type': 'string',
            'required': False
        }
    ],
    'responses': {
        '200': {
            'description': 'Application submitted successfully'
        },
        '500': {
            'description': 'Database error'
        }
    }
})
def submit_application():
    """Handle form submission and save data using SQLAlchemy."""
    if request.method == 'POST':
        try:
            first_name = request.form.get('first-name')
            last_name = request.form.get('last-name')
            email = request.form.get('email')
            grant_type = request.form.get('grant-type')
            funding_amount = float(request.form.get('funding-amount', 0))
            special_award = request.form.get('special-award-checkbox') == "on"
            award_details = request.form.get('special-award-details')

            application_form = ApplicationForm(
                first_name=first_name,
                last_name=last_name,
                email=email,
                grant_type=grant_type,
                funding_amount=funding_amount,
                special_award=special_award,
                award_details=award_details
            )

            db.session.add(application_form)
            db.session.commit()
            print("Data successfully saved to database!")

        except SQLAlchemyError as e:
            db.session.rollback()
            print("Error inserting into database:", str(e))
            return jsonify(error=str(e), message="Failed to process request"), 500

        return redirect(url_for('home'))

    return "Invalid Request", 400


"""
if __name__ == "__main__":
    if 'localhost' in request.host or '127.0.0.1' in request.host:
        # Run with debug mode but without SSL for local development
        application.run(host="0.0.0.0", port=5000, debug=True)
    else:
        # Run with SSL for development testing of HTTPS
        application.run(
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            ssl_context='adhoc'  # Uses a self-signed certificate
        )
"""
if __name__ == "__main__":
    is_local = os.getenv("FLASK_ENV", "production") == "development"
    
    if is_local:
        application.run(host="0.0.0.0", port=5000, debug=True)
    else:
        application.run(
            host="0.0.0.0", 
            port=5000, 
            debug=False, 
            ssl_context='adhoc'  # Uses a self-signed certificate
        )
