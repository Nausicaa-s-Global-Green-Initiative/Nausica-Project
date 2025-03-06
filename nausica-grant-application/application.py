"""Basic Flask application for rendering web pages."""

import os
import pymysql
import time
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate
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

class GrantApplication(db.Model):
    __tablename__ = 'application_form'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    grant_type = db.Column(db.String(100), nullable=False)
    funding_amount = db.Column(db.Float, nullable=False)
    special_award = db.Column(db.Boolean, default=False)
    award_details = db.Column(db.Text)

    def __init__(self, first_name, last_name, email, grant_type, funding_amount, special_award, award_details):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.grant_type = grant_type
        self.funding_amount = funding_amount
        self.special_award = special_award
        self.award_details = award_details

# Initialize Flask Migrate
migrate = Migrate(application, db)

def get_db_credentials():
    """Load database credentials from environment variables."""
    return {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "port": int(os.getenv("DB_PORT", 3306))  # Default to 3306
    }

def create_sql_connection(retries=5, delay=2):
    db_credentials = get_db_credentials()
    connection = None

    for attempt in range(retries):
        try:
            # Connect to MySQL using env variables
            connection = pymysql.connect(
                host=db_credentials["host"],
                user=db_credentials["user"],
                password=db_credentials["password"],
                database=db_credentials["database"],
                port=db_credentials["port"],
                cursorclass=pymysql.cursors.DictCursor
            )
            break  # Exit loop if connection is successful
        except pymysql.Error as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            time.sleep(delay)  # Wait before retrying

    return connection

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
            application_form = GrantApplication(
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
    return render_template('application.html')

@application.route('/listview')
def listview():
    """Retrieve all records and display in an HTML page using SQLAlchemy."""
    try:
        records = GrantApplication.query.all()
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

        print("Received POST request!")

        # Retrieve form data
        first_name = request.form.get('first-name')
        last_name = request.form.get('last-name')
        email = request.form.get('email')
        grant_type = request.form.get('grant-type')
        funding_amount = request.form.get('funding-amount')
        special_award = 1 if request.form.get('special-award-checkbox') == "on" else 0
        award_details = request.form.get('special-award-details')

        print(f"Saving to DB: {first_name, last_name, email, grant_type, funding_amount, special_award, award_details}")

        connection = None
        try:
            # Connect to MySQL using env variables
            connection = create_sql_connection()

            if connection:
                with connection.cursor() as cursor:
                    sql_query = """
                    INSERT INTO application_form (first_name, last_name, email, grant_type, funding_amount, special_award, award_details)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_query, (first_name, last_name, email, grant_type, float(funding_amount), special_award, award_details))
                    connection.commit()

                print("Data successfully saved to AWS RDS!")
            else:
                print("Failed to establish database connection.")

        except pymysql.Error as e:
            print("Error inserting into database:", str(e))
            if connection:
                connection.rollback()  # Rollback in case of error

        finally:
            if connection:
                connection.close()  # Ensure connection is closed properly


        return redirect(url_for('home'))

    return "Invalid Request", 400


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000)
