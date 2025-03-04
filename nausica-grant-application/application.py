"""Basic Flask application for rendering web pages."""
import os, pymysql
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger

application = Flask(__name__)
swagger = Swagger(application)

# Load environment variables from .env file
load_dotenv()


"Set up database configuration"
application.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 3306)}/{os.getenv('DB_NAME')}"
)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(application)

class GrantApplication(db.Model):
    __tablename__ = 'application_form'

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


@application.route("/", methods=['GET', 'POST'])
def home():
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
    """Return a message and a 400 error code to the user."""
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


@application.route('/apply')
def apply():
    """Render the application.html page."""
    return render_template('application.html')

@application.route('/listview')
def listview():
    """Render the application.html page."""
    return render_template('listview.html')


@application.route('/submit', methods=['POST'])
def submit_application():
    """Handle form submission and save data to AWS RDS"""

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

        print(f"Saving to DB: {first_name}, {last_name}, {email}, {grant_type}, {funding_amount}, {special_award}, {award_details}")

        try:
            # Load database credentials from .env
            db_host = os.getenv("DB_HOST")
            db_user = os.getenv("DB_USER")
            db_password = os.getenv("DB_PASSWORD")
            db_name = os.getenv("DB_NAME")
            db_port = int(os.getenv("DB_PORT", 3306))  # Default to 3306

            #  Establish MySQL connection using environment variables
            connection = pymysql.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name,
                port=db_port,
                cursorclass=pymysql.cursors.DictCursor
            )

            with connection.cursor() as cursor:
                sql_query = """
                INSERT INTO application_form (first_name, last_name, email, grant_type, funding_amount, special_award, award_details)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_query, (first_name, last_name, email, grant_type, float(funding_amount), special_award, award_details))
                connection.commit()

            print("Data successfully saved to AWS RDS!")

        except pymysql.Error as e:
            print("Error inserting into database:", str(e))
            connection.rollback()  # Rollback in case of error

        finally:
            connection.close()  # Ensure connection is closed properly

        return redirect(url_for('home'))

    return "Invalid Request", 400

if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5000)  
