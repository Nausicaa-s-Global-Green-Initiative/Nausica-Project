from .application import db

class ApplicationForm(db.Model):
    grant_application_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    grant_type = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<ApplicationForm {self.first_name}>'
