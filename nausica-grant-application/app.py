from flask import Flask, render_template
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

@app.route("/")
def home():
    """
    Home Page
    ---
    tags:
      - Pages
    summary: Render the home page
    description: Renders the home page using the 'home.html' template.
    responses:
      200:
        description: Successfully rendered home page.
    """
    return render_template("home.html")


@app.route("/about")
def about():
    """
    About Page
    ---
    tags:
      - Pages
    summary: Render the about page
    description: Renders the about page using the 'about.html' template.
    responses:
      200:
        description: Successfully rendered about page.
    """
    return render_template("about.html")