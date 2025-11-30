"""
Supabase client configuration for STEALTH-TINKO
Provides centralized Supabase client management
"""

from supabase import create_client, Client
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Global Supabase client instance
_supabase_client: Client = None


def get_supabase_client() -> Client:
    """Get or create Supabase client instance"""
    global _supabase_client

    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise ValueError("Supabase URL and ANON key must be configured in settings")

        try:
            _supabase_client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_ANON_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    return _supabase_client


def get_supabase_admin_client() -> Client:
    """Get Supabase client with service role key for admin operations"""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("Supabase URL and SERVICE_ROLE_KEY must be configured for admin operations")

    try:
        client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
        )
        logger.info("Supabase admin client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase admin client: {e}")
        raise


# Convenience functions for common operations
def get_current_user(token: str = None):
    """Get current user from Supabase auth"""
    client = get_supabase_client()
    return client.auth.get_user(token)


def sign_out_current_user():
    """Sign out current user"""
    client = get_supabase_client()
    return client.auth.sign_out()
