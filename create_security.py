# create_security.py

import os

files = {}

# ── Security config ─────────────────────────────────────────────
files["api/security.py"] = """
# api/security.py

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.logger import get_logger

logger = get_logger("Security")

# Secret key — in production this must come from environment variable
SECRET_KEY  = "finplatform-dev-secret-change-in-production-2024"
ALGORITHM   = "HS256"
TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

# Simple in-memory API key store for now
# In production this would be a database
VALID_API_KEYS = {
    "demo-key-12345"  : {"user": "demo",  "role": "read"},
    "admin-key-99999" : {"user": "admin", "role": "admin"},
}


def verify_api_key(key: str) -> Optional[dict]:
    return VALID_API_KEYS.get(key)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide Bearer token or API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Check if it's an API key first
    key_data = verify_api_key(token)
    if key_data:
        logger.info(f"API key auth: user={key_data['user']}")
        return key_data

    # Otherwise treat as JWT token
    payload = verify_token(token)
    if payload:
        logger.info(f"JWT auth: user={payload.get('user')}")
        return payload

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def optional_auth(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
) -> Optional[dict]:
    if not credentials:
        return None
    token = credentials.credentials
    key_data = verify_api_key(token)
    if key_data:
        return key_data
    return verify_token(token)
"""

# ── Rate limiter setup ──────────────────────────────────────────
files["api/limiter.py"] = """
# api/limiter.py

from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter — identifies clients by IP address
limiter = Limiter(key_func=get_remote_address)
"""

# ── Input sanitizer ─────────────────────────────────────────────
files["api/sanitizer.py"] = """
# api/sanitizer.py

import re
from fastapi import HTTPException


def sanitize_symbol(symbol: str) -> str:
    \"\"\"
    Clean and validate a stock symbol or company name.
    Allows letters, numbers, dots, hyphens (for symbols like BRK-B, RELIANCE.NS)
    Max 30 chars to prevent abuse.
    \"\"\"
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol cannot be empty")

    symbol = symbol.strip()

    if len(symbol) > 30:
        raise HTTPException(
            status_code=400,
            detail="Symbol too long. Maximum 30 characters."
        )

    # Allow letters, numbers, dots, hyphens, spaces (for company names)
    if not re.match(r'^[A-Za-z0-9\\s.\\-&]+$', symbol):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid characters in symbol: '{symbol}'"
        )

    return symbol


def sanitize_query(query: str) -> str:
    \"\"\"Clean search query — strip dangerous characters.\"\"\"
    if not query:
        return ""
    query = query.strip()[:50]  # max 50 chars
    # Remove any special chars except letters, numbers, spaces
    query = re.sub(r'[^A-Za-z0-9\\s.\\-&]', '', query)
    return query


def sanitize_exchange(exchange: str) -> str:
    \"\"\"Only allow known exchange values.\"\"\"
    allowed = {"NSE", "BSE", "US"}
    exchange = exchange.upper().strip()
    if exchange not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exchange. Allowed: NSE, BSE, US"
        )
    return exchange
"""

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Written: {path}")

print("\nSecurity files created!")