"""Database models for the grant application system."""
from datetime import datetime
from db_config import db
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func


class ApplicationForm(db.Model):
    """Model representing a grant application form submission."""
    # Table configuration
    __tablename__ = 'application_form'
    
    # Primary identifier
    grant_application_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Basic applicant information
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    
    # Grant details
    grant_type = db.Column(db.String(120), nullable=False)
    funding_amount = db.Column(db.Float, nullable=False, default=0.0)
    special_award = db.Column(db.Boolean, default=False)
    award_details = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(50), default='Pending')
    
    def __init__(self, first_name, last_name, email, grant_type, 
                 funding_amount=0.0, special_award=False, award_details=None):
        """Initialize a new application form record."""
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.grant_type = grant_type
        self.funding_amount = funding_amount
        self.special_award = special_award
        self.award_details = award_details
    
    def __repr__(self):
        """Provide a readable representation of the application."""
        return f'<ApplicationForm {self.first_name} {self.last_name}: {self.grant_type}>'
    
    @property
    def full_name(self):
        """Return the applicant's full name."""
        return f'{self.first_name} {self.last_name}'
    
    def to_dict(self):
        """Convert the application to a dictionary for API responses."""
        return {
            'id': self.grant_application_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'grant_type': self.grant_type,
            'funding_amount': self.funding_amount,
            'special_award': self.special_award,
            'award_details': self.award_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status
        }


class ApplicationLog(db.Model):
    """Model for application logs table."""
    __tablename__ = 'application_logs'
    
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False, index=True)
    log_level = db.Column(db.String(10), nullable=False, index=True)  # INFO, WARNING, ERROR, etc.
    message = db.Column(db.Text, nullable=False)
    
    # Optional additional fields for better debugging
    user_id = db.Column(db.String(255), nullable=True)  # User who triggered the action (if applicable)
    source = db.Column(db.String(255), nullable=True)  # Component that generated the log
    
    def __repr__(self):
        return f"<Log {self.log_id}: [{self.log_level}] {self.message[:50]}{'...' if len(self.message) > 50 else ''}>"
