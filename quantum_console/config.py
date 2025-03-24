import os

class Config:
    """Configuration settings for the Flask application."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_secret_key'
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1']
    # Add other configuration variables as needed 