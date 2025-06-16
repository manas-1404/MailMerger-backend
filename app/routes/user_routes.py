from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dbConnection import get_db_session
from app.models.user_models import User
from app.pydantic_schemas.response_pydantic import ResponseSchema
from app.pydantic_schemas.user_pydantic import UserSchema
from app.utils.utils import encrypt_string

user_router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)

@user_router.post("/add-user")
def add_user(user_data: UserSchema, db_connection: Session = Depends(get_db_session)):
    """
    Endpoint to add a new user.
    This is a placeholder endpoint for demonstration purposes.
    """

    existing_user = db_connection.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        return ResponseSchema(
            status_code=409,
            success=False,
            message="User already exists with this email.",
        )

    user = User(
        name=user_data.name,
        email=user_data.email,
        password=encrypt_string(user_data.password),
        resume=user_data.resume,
        cover_letter=user_data.cover_letter
    )

    db_connection.add(user)

    db_connection.commit()

    return ResponseSchema(
        status_code=201,
        success=True,
        message="User added successfully.",
        data={"uid": user.uid, "name": user.name, "email": user.email}
    )
