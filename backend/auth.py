import logging
import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("hawala")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    expected = os.getenv("API_AUTH_TOKEN")
    if not expected:
        log.warning("API_AUTH_TOKEN is not set — authentication is DISABLED")
        return "local-dev"
    if not api_key or api_key != expected:
        log.warning("Unauthorized API access attempt with key: %s", api_key[:8] + "..." if api_key else "None")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    log.info("Authenticated API request from key: %s", api_key[:8] + "...")
    return api_key
