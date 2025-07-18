import redis
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from starlette import status

from app.auth.dependency_auth import create_jwt_token, create_jwt_refresh_token
from app.db.dbConnection import get_db_session
from app.db.redisConnection import get_redis_connection
from app.models import User, Template
from app.pydantic_schemas.login_pydantic import LoginSchema
from app.pydantic_schemas.response_pydantic import ResponseSchema
from app.pydantic_schemas.template_pydantic import TemplateSchema
from app.utils.utils import verify_string, serialize_for_redis

login_router = APIRouter(
    prefix="/api/auth",
    tags=["Login"]
)

@login_router.post("/login")
def login(login_data: LoginSchema, db_connection: Session = Depends(get_db_session), redis_connection: redis.Redis = Depends(get_redis_connection)):

    user = (db_connection.query(User).options(joinedload(User.templates)).filter(User.email == login_data.email).first())

    #user is present in the db
    if user is None or not verify_string(plain_string=login_data.password, hashed_string=user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")


    user_jwt_token = create_jwt_token(data=user.uid)

    user_refresh_token = create_jwt_refresh_token(data=user.uid)

    db_connection.query(User).filter(User.uid == user.uid).update({User.refresh_token: user_refresh_token})

    db_connection.commit()

    #cache all the user templates as soon as they login to prevent future database queries for templates
    redis_template_key = f"user:{user.uid}:templates"
    redis_pipeline = redis_connection.pipeline()

    for template in user.templates:
        template_data = TemplateSchema.model_validate(template).model_dump()
        redis_pipeline.hset(redis_template_key, template.template_id, serialize_for_redis(template_data))

    redis_pipeline.expire(redis_template_key, 60 * 90)
    redis_pipeline.execute()

    json_response = JSONResponse(
        content= ResponseSchema(
            success=True,
            status_code=200,
            message="Login successful!",
            data={
                "jwt_token": user_jwt_token,
            }
        ).model_dump()
    )

    json_response.set_cookie(
        key="refresh_token",
        value=user_refresh_token,
        httponly=True,
        secure=False,  # Set to True in production
        samesite="Strict",
        max_age=60 * 60 * 24 * 7
    )

    return json_response
