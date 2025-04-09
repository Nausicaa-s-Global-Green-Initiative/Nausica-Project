"""Basic Flask application for rendering web pages."""

import os, time
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate
from flasgger import Swagger, swag_from
from flask_login import login_required
from db_config import db  # Import db from db_config
from models import ApplicationForm 
from flask_wtf.csrf import CSRFProtect
from db_logger import AppLogger
from werkzeug.security import check_password_hash, generate_password_hash
import secrets

# Load environment variables from .env file
load_dotenv()

application = Flask(__name__)
application.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(16))
swagger = Swagger(application)

# Create and initialize CSRF protection
csrf = CSRFProtect(application)

# Admin credentials from environment variables (no defaults for security)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = None

# If admin password is in environment, hash it at startup
if os.getenv("ADMIN_PASSWORD"):
    ADMIN_PASSWORD_HASH = generate_password_hash(os.getenv("ADMIN_PASSWORD"))

# Display warning if credentials are not set
if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
    print("WARNING: Admin credentials not configured. Set ADMIN_USERNAME and ADMIN_PASSWORD environment variables.")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(application)
login_manager.login_view = "admin_login_get"  # Redirects unauthorized users to login page

# User class for authentication
class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Set up database configuration
application.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 3306)}/{os.getenv('DB_NAME')}"
)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(application)  # Initialize db with app

# Initialize Flask Migrate
migrate = Migrate(application, db)

@application.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to return a 200 status."""
    return jsonify(status="OK"), 200

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
    AppLogger.warning(f"Bad request: {request.path}", source="error_handler")
    return "Bad Request: Check terminal for more details.", 400

@application.route("/about")
def about():
    """Render the about page using the 'about.html' template."""
    return render_template("about.html")

@application.route('/apply')
def apply():
    """Render the application.html page."""
    session['visited_apply'] = True
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

@application.route('/admin/login', methods=['GET'])
def admin_login_get():
    """Render the admin login page for GET requests."""
    return render_template('admin_login.html')

@application.route('/admin/login', methods=['POST'])
def admin_login():
    """Authenticate using simple username/password"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "Missing credentials!", 400

        try:
            # Check if admin credentials are configured
            if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
                AppLogger.error("Admin login attempted but credentials not configured", source="admin_login")
                return "Admin login not configured", 500
            
            # Simple username and password validation
            if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
                # Login successful
                user = User(username)
                login_user(user)
                session['username'] = username  # Store username in session
                
                AppLogger.info(f"Admin user {username} successfully authenticated", source="admin_login")
                return redirect(url_for('listview'))
            else:
                # Add a small delay to prevent brute force attacks
                time.sleep(1)
                AppLogger.warning(f"Failed login attempt for username: {username}", source="admin_login")
                return "Authentication failed: Invalid credentials", 401
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            AppLogger.error(f"Authentication failed: {str(e)}", source="admin_login")
            return "Authentication failed: Error during login", 500

    return render_template('admin_login.html')

@application.route('/admin')
@login_required
def admin_dashboard():
    return f"Welcome to the Admin Panel! Logged in as: {session.get('username')}."

@application.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop("username", None)  # Remove user data from session
    return redirect(url_for('home'))

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
        # Debug: Print the form data
        print("Form data:", request.form)
        print("Files:", request.files)
        
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
            
            AppLogger.info(f"Application submitted by {first_name} {last_name}", 
                          user_id=email, 
                          source="submit_application")
            
        except SQLAlchemyError as e:
            db.session.rollback()
            AppLogger.exception("Failed to submit application", exc=e, source="submit_application")
            return jsonify(error=str(e), message="Failed to process request"), 500

        return redirect(url_for('home'))

    return "Invalid Request", 400

if __name__ == "__main__":
    is_local = os.getenv("FLASK_ENV", "production") == "development"
    
    if is_local:
        application.run(host="0.0.0.0", port=5000, debug=True)
    else:
        application.run(host="0.0.0.0", port=5000)
