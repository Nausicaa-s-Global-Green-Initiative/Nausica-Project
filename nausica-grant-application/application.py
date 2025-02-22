"""Basic Flask application for rendering web pages."""
import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

application = Flask(__name__)

"Set up database configuration"
application.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(application)

@application.route("/")
def home():
    """Render the home page using the 'home.html' template."""
    return render_template("home.html")


@application.route("/about")
def about():
    """Render the about page using the 'about.html' template."""
    return render_template("about.html")
