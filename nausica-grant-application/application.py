"""Basic Flask application for rendering web pages."""
import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate
from dotenv import load_dotenv
from flasgger import Swagger

# Load environment variables from .env file
load_dotenv()


application = Flask(__name__)
swagger = Swagger(application)

# Set up database configuration
application.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 3306)}/{os.getenv('DB_NAME')}"
)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(application)

# Initialize Flask Migrate
migrate = Migrate(application, db)

@application.route("/", methods=['GET', 'POST'])
def home():
    """Handle POST requests for form submissions."""
    from .models import ApplicationForm  # Use absolute import
    """
    
    Handle POST requests for form submissions.
    ---
    tags:
      - Home
    parameters:
      - name: first_name
        in: formData
        type: string
        required: true
        description: First name of the user.
      - name: last_name
        in: formData
        type: string
        required: true
        description: Last name of the user.
      - name: email
        in: formData
        type: string
        required: true
        description: Email address of the user.
      - name: grant_type
        in: formData
        type: string
        required: true
        description: Type of grant being applied for.
    responses:
      200:
        description: Successfully received form data.
      400:
        description: Bad request due to missing or invalid data.
    
    """
    if request.method == 'POST':
        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            grant_type = request.form['grant_type']
        
            """Create an instance of ApplicationForm model with the form submission data"""
            application_form = ApplicationForm(
                first_name=first_name,
                last_name=last_name,
                email=email,
                grant_type=grant_type
            )
        
            """Add the new form data to the database session"""
            db.session.add(application_form)
        
            """Commit the session to save data to the database"""
            db.session.commit()
            return jsonify(message="Form data has been saved successfully"), 200
        except SQLAlchemyError as e:
            """This block will handle exceptions from the try block"""
            db.session.rollback()
            return jsonify(error=str(e), message="Failed to process request"), 500
        
        # For debug to print values to terminal, comment out when live
        # print(f"Received: {first_name}, {last_name}, {email}, {grant_type}")

        # Process the data
        # return f"Received: {first_name}, {last_name}, {email}, {grant_type}"
        
    """Render the home page using the 'home.html' template for GET requests and for any other non-POST method."""
    return render_template("home.html")

@application.errorhandler(400)
def handle_bad_request(e):
    """Log the error and the form data when a bad request happens.
    
    Handle 400 Bad Request errors.

    ---
    tags:
      - Errors
    responses:
      400:
        description: Bad request due to invalid form submission.
    
    """
    print("Failed to process request:", request.form)
    return "Bad Request: Check terminal for more details.", 400

@application.route("/about")
def about():
    """Render the about page using the 'about.html' template.
    
    ---
    tags:
      - About
    responses:
      200:
        description: Render the about page.
    
    """
    return render_template("about.html")


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5000)  # Adjust host/port if needed
