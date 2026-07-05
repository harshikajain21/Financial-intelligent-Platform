# api/routes/auth.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
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
async def get_token(request: TokenRequest):
    """
    Exchange a valid API key for a JWT access token.
    Use the token in Authorization: Bearer <token> header.
    """
    key_data = verify_api_key(request.api_key)
    if not key_data:
        logger.warning(f"Invalid API key attempt")
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
    """Returns info about the currently authenticated user."""
    return {
        "user"          : current_user.get("user"),
        "role"          : current_user.get("role"),
        "authenticated" : True
    }