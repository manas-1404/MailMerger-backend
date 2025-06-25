import json
from collections import defaultdict
from email.policy import default

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import redis

from app.models import User, Email
from app.pydantic_schemas.email_pydantic import EmailSchema
from app.auth.dependency_auth import authenticate_request
from app.db.dbConnection import get_db_session
from app.db.redisConnection import get_redis_connection
from app.pydantic_schemas.response_pydantic import ResponseSchema

queue_router = APIRouter(
    prefix="/api/queue",
    tags=["Queue"]
)

@queue_router.get("/get-email-queue")
def get_email_queue(jwt_payload: dict = Depends(authenticate_request),
                    db_connection: Session = Depends(get_db_session),
                    redis_connection: redis.Redis = Depends(get_redis_connection)):
    """
    Endpoint to get the email queue for the authenticated user.
    """

    user_id = jwt_payload.get("sub")

    user = db_connection.query(User).filter(User.uid == user_id).first()

    if not user:
        return ResponseSchema(
            success=False,
            status_code=404,
            message="User not found.",
            data={}
        )

    redis_hash_key = user.uid
    redis_hash_value = redis_connection.hget("users", redis_hash_key)

    if redis_hash_value:
        email_queue = redis_connection.lrange(redis_hash_value, 0, -1)
        emails = [json.loads(email) for email in email_queue]

        return ResponseSchema(
            success=True,
            status_code=200,
            message="Email queue retrieved successfully from Redis.",
            data={"queue_length": len(emails), "emails": emails}
        )

    else:
        #searching in db
        email_queue = db_connection.query(Email).filter((Email.uid == user_id) & (Email.is_sent == False)).all()

        #add the emails to redis for future requests
        redis_hash_key = user.uid
        redis_hash_value = f"email_queue:{user.uid}"

        redis_connection.hset("users", redis_hash_key, redis_hash_value)

        email_list = []

        for email in email_queue:
            email_dict = EmailSchema.model_validate(email).model_dump()
            email_dict["from_email"] = user.email
            redis_connection.rpush(redis_hash_value, json.dumps(email_dict))
            email_list.append(email_dict)

        return ResponseSchema(
            success=True,
            status_code=200,
            message="Email queue retrieved successfully from DB (not found in Redis).",
            data={"queue_length": len(email_list), "all_emails": email_list}
        )


@queue_router.post("/add-to-queue")
def add_to_queue(email: EmailSchema, jwt_payload: dict = Depends(authenticate_request),
                 db_connection: Session = Depends(get_db_session),
                 redis_connection: redis.Redis = Depends(get_redis_connection)):
    """
    Endpoint to add an email to the processing queue.
    """
    user_id = jwt_payload.get("sub")

    user = db_connection.query(User).filter(User.uid == user_id).first()

    if not user:
        return ResponseSchema(
            success=False,
            status_code=404,
            message="User not found.",
            data={}
        )

    redis_hash_key = user.uid
    redis_hash_value = f"email_queue:{user.uid}"     #this hash value will act as a pointer to the email queue for each user

    redis_connection.hset("users", redis_hash_key, redis_hash_value)

    email_dict = email.model_dump()
    email_dict["from_email"] = user.email

    redis_connection.rpush(redis_hash_value, json.dumps(email_dict))

    return ResponseSchema(
        success=True,
        status_code=200,
        message="Email added to the queue successfully.",
        data={"queue_length": redis_connection.llen(redis_hash_value)}
    )
