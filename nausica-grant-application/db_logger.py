from models import ApplicationLog
from db_config import db
import traceback
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, OperationalError

class AppLogger:
    """Utility class to log messages to the application_logs table."""
    
    @staticmethod
    def log(level, message, user_id=None, source=None, max_retries=3):
        """
        Log a message to the database with retry logic.
        """
        retry_count = 0
        last_error = None
        
        # Truncate very long messages to prevent database issues
        if len(message) > 65000:  # MySQL text field limit
            message = message[:65000] + "... [truncated]"
        
        while retry_count < max_retries:
            try:
                # Just use the regular session directly
                log_entry = ApplicationLog(
                    log_level=level.upper(),
                    message=message,
                    user_id=user_id,
                    source=source,
                    timestamp=datetime.now()
                )
                
                db.session.add(log_entry)
                db.session.commit()
                return True  # Success
                
            except OperationalError as e:
                # Handle database connection errors specifically
                last_error = e
                retry_count += 1
                
                print(f"Database connection error (attempt {retry_count}/{max_retries}): {str(e)}")
                
                try:
                    # Use db.session instead of session
                    db.session.rollback()
                except:
                    pass
                
            except SQLAlchemyError as e:
                # Handle other database-related errors
                last_error = e
                retry_count += 1
                
                print(f"Database error (attempt {retry_count}/{max_retries}): {str(e)}")
                
                try:
                    # Use db.session instead of session
                    db.session.rollback()
                except:
                    pass
                
            except Exception as e:
                # Handle unexpected errors
                last_error = e
                retry_count += 1
                
                print(f"Unexpected error (attempt {retry_count}/{max_retries}): {str(e)}")
                
                try:
                    # Use db.session instead of session
                    db.session.rollback()
                except:
                    pass
        
        # If we got here, all retries failed - log to console as fallback
        print(f"Failed to log to database after {max_retries} attempts: {str(last_error)}")
        print(f"Original log: [{level}] {message}")
        return False
    
    @classmethod
    def info(cls, message, user_id=None, source=None):
        """Log an info message."""
        cls.log("INFO", message, user_id, source)
    
    @classmethod
    def warning(cls, message, user_id=None, source=None):
        """Log a warning message."""
        cls.log("WARNING", message, user_id, source)
    
    @classmethod
    def error(cls, message, user_id=None, source=None):
        """Log an error message."""
        cls.log("ERROR", message, user_id, source)
    
    @classmethod
    def exception(cls, message, exc=None, user_id=None, source=None):
        """Log an exception with traceback."""
        if exc:
            tb = traceback.format_exc()
            full_message = f"{message}\nException: {str(exc)}\n{tb}"
        else:
            full_message = message
            
        cls.log("ERROR", full_message, user_id, source)