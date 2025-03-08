"""Basic Flask application for rendering web pages."""

import os
import pymysql
import time
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate
from flasgger import Swagger

# Load environment variables from .env file
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from db_config import db  # Import db from db_config
from models import ApplicationForm  

application = Flask(__name__)
application.secret_key = os.getenv("FLASK_SECRET_KEY")
swagger = Swagger(application)

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

@application.route('/listview')
def listview():
    """Retrieve all records and display in an HTML page using SQLAlchemy."""
    try:
        records = ApplicationForm.query.all()
    except SQLAlchemyError as e:
        print("Error fetching data:", str(e))
        records = []

    return render_template('listview.html', records=records)



@application.route('/logout')
def logout():
    """Dummy logout route to prevent BuildError."""
    return redirect(url_for('home'))

@application.route('/submit', methods=['POST'])
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

