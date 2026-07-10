# fix_auth.py

content = """
# api/routes/auth.py

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from api.limiter import limiter
from api.security import verify_api_key, create_access_token, get_current_user
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("AuthRouter")


class TokenRequest(BaseModel):
    api_key: str


class TokenResponse(BaseModel):
    access_token : str
    token_type   : str
    expires_in   : str


@router.post(
    "/auth/token",
    response_model=TokenResponse,
    summary="Exchange API key for JWT token"
)
@limiter.limit("10/minute")
async def get_token(request: Request, request_body: TokenRequest):
    key_data = verify_api_key(request_body.api_key)
    if not key_data:
        logger.warning("Invalid API key attempt")
        raise HTTPException(status_code=401, detail="Invalid API key")
    token = create_access_token({"user": key_data["user"], "role": key_data["role"]})
    logger.info(f"Token issued for user: {key_data['user']}")
    return TokenResponse(
        access_token = token,
        token_type   = "bearer",
        expires_in   = "24 hours"
    )


@router.get(
    "/auth/me",
    summary="Get current authenticated user info"
)
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "user"          : current_user.get("user"),
        "role"          : current_user.get("role"),
        "authenticated" : True
    }
"""

with open("api/routes/auth.py", "w", encoding="utf-8") as f:
    f.write(content.strip())
    print("api/routes/auth.py fixed")