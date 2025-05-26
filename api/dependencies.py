"""
API dependencies for authentication and other shared functionality
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

import service
from core.config import settings

logger = service.logger

# Security - API key authentication
API_KEY = settings.api_key
if not API_KEY:
    logger.warning("No API key set - running without "
                   "authentication (DEVELOPMENT ONLY!)")

api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key: str = Security(api_key_header)):
    """Validate API key for authentication"""
    if not API_KEY:
        # Skip authentication (DEVELOPMENT ONLY!)
        logger.warning("No API_KEY set - running without authentication")
        return api_key
    if api_key != API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key
