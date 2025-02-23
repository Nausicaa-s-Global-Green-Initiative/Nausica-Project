"""Basic Flask application for rendering web pages."""
import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

application = Flask(__name__)

"Set up database configuration"
application.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(application)

@application.route("/", methods=['GET', 'POST'])
def home():
    """Handle POST requests for form submissions."""
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        grant_type = request.form['grant_type']
        
        "For debug to print values to terminal, comment out when live"
        #print(f"Received: {first_name}, {last_name}, {email}, {grant_type}")

        "Process the data"
        return f"Received: {first_name}, {last_name}, {email}, {grant_type}"

    """Render the home page using the 'home.html' template."""
    return render_template("home.html")

@application.errorhandler(400)
def handle_bad_request(e):
    """Log the error and the form data when a bad request happens."""
    print("Failed to process request:", request.form)
    """Return a message and a 400 error code to the user."""
    return "Bad Request: Check terminal for more details.", 400

@application.route("/about")
def about():
    """Render the about page using the 'about.html' template."""
    return render_template("about.html")
