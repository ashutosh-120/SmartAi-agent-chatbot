"""
backend/database.py - Supabase Client Initialization
"""

import logging
from supabase import create_client, Client
from config import settings

logger = logging.getLogger(__name__)

# Initialize the Supabase client
# We use the Service Role key for backend operations so we can bypass RLS for data storage
_url: str = settings.SUPABASE_URL
_key: str = settings.SUPABASE_SERVICE_ROLE_KEY

db: Client = None

if _url and _key:
    try:
        db = create_client(_url, _key)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.error("Failed to initialize Supabase client: %s", e)
else:
    logger.warning("Supabase configuration missing (SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY). Database features disabled.")

def get_db() -> Client:
    """Dependency for routes that need the database."""
    if db is None:
        raise RuntimeError("Database not configured. Check your .env file.")
    return db
