"""
config.py - Application configuration
Loads environment variables from .env file using python-dotenv.
"""

import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()


class Settings:
    """Central config object — import this everywhere."""

    # Google Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # GitHub
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # General
    APP_NAME: str = os.getenv("APP_NAME", "SmartAI Agent Chatbot")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "")

    # Gemini model to use — gemini-2.0-flash is the current stable GA model
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # GitHub API base URL
    GITHUB_API_BASE: str = "https://api.github.com"

    def validate(self):
        """Raise a clear error if required keys are missing."""
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in your .env file.")
        return True


# Singleton settings instance
settings = Settings()

