from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from starlette import status

from app.auth.dependency_auth import create_jwt_token, create_jwt_refresh_token
from app.db.dbConnection import get_db_session
from app.models import User
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
    # refresh_token = request.cookies.get("refresh_token")

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header."
        )

    refresh_token = auth_header.split("Bearer ")[1]

    print("Received refresh token:", refresh_token)

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided in Authorization header."
        )

    try:
        decoded_refresh_token = jwt.decode(
            token=refresh_token,
            key=settings.JWT_SIGNATURE_SECRET_KEY,
            algorithms=[settings.JWT_AUTH_ALGORITHM],
            options={"verify_sub": False}
        )

        user_id = decoded_refresh_token.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload."
            )

        print("Decoded user ID from refresh token:", user_id, "\nType:", type(user_id))

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

    except JWTError as e:
        print("JWTError:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token. Please log in again."
        )


@auth_router.get("/renew-refresh-and-jwt-token")
def renew_refresh_and_jwt_token(request: Request, db_connection: Session = Depends(get_db_session)):
    """
    Endpoint to refresh the JWT token.
    This endpoint should be called when the JWT token is about to expire.
    """
    # refresh_token = request.cookies.get("refresh_token")

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header."
        )

    expired_refresh_token = auth_header.split("Bearer ")[1]

    print("Received expired refresh token:", expired_refresh_token)

    if not expired_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided in Authorization header."
        )

    try:
        decoded_refresh_token = jwt.decode(
            token=expired_refresh_token,
            key=settings.JWT_SIGNATURE_SECRET_KEY,
            algorithms=[settings.JWT_AUTH_ALGORITHM],
            options={"verify_sub": False, "verify_exp": False}
        )

        user_id = decoded_refresh_token.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload."
            )

        user = db_connection.query(User).filter(User.uid == user_id, User.jwt_refresh_token == expired_refresh_token).first()

        print("Decoded user ID from expired refresh token:", user_id, "\nType:", type(user_id))

        new_jwt_token = create_jwt_token(data=user_id)
        new_refresh_token = create_jwt_refresh_token(data=user_id)

        user.jwt_refresh_token = new_refresh_token

        db_connection.commit()

        return ResponseSchema(
            success=True,
            status_code=200,
            message="JWT token refreshed successfully.",
            data={"jwt_token": new_jwt_token, "refresh_token": new_refresh_token}
        )

    except JWTError as e:
        print("JWTError:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token. Please log in again."
        )