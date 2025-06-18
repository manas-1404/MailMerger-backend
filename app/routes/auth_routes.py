from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import APIRouter, Request, HTTPException
from starlette import status

from app.auth.dependency_auth import create_jwt_token
from app.pydantic_schemas.response_pydantic import ResponseSchema
from app.utils.config import settings


auth_router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

@auth_router.get("/refresh-jwt-token")
def refresh_jwt_token(request: Request):
    """
    Endpoint to refresh the JWT token.
    This endpoint should be called when the JWT token is about to expire.
    """
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookies."
        )

    try:
        decoded_refresh_token = jwt.decode(
            token=refresh_token,
            key=settings.JWT_SIGNATURE_SECRET_KEY,
            algorithms=[settings.JWT_AUTH_ALGORITHM],
        )

        user_id = decoded_refresh_token.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload."
            )

        new_jwt_token = create_jwt_token(data=user_id)

        return ResponseSchema(
            success=True,
            status_code=200,
            message="JWT token refreshed successfully.",
            data={"jwt_token": new_jwt_token}
        )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again."
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token. Please log in again."
        )