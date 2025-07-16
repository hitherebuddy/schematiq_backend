import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a-very-secret-key')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # In a real app, this would point to a database URI
    # For now, we'll use an in-memory dictionary as a mock DB
    DATABASE = {
        "users": {},
        "plans": {}
    }