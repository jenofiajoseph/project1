import os
from dotenv import load_dotenv

# Load variables from .env if it exists
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-12345")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///lms.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
