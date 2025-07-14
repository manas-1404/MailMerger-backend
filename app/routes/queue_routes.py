import json
from collections import defaultdict
from datetime import datetime
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
from app.utils.utils import generate_eid

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

    redis_email_queue_key = f"email_queue:{user_id}"
    email_queue = redis_connection.lrange(redis_email_queue_key, 0, -1)

    if email_queue:

        emails = [json.loads(email) for email in email_queue]

        redis_connection.expire(redis_email_queue_key, 90*60) #extend the expiry time of the email queue because it was recently used

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
        email_list = []

        for email in email_queue:
            email_dict = EmailSchema.model_validate(email).model_dump()
            email_dict["from_email"] = user.email
            redis_connection.rpush(redis_email_queue_key, json.dumps(email_dict))
            email_list.append(email_dict)

        redis_connection.expire(redis_email_queue_key, 90*60)

        return ResponseSchema(
            success=True,
            status_code=200,
            message="Email queue retrieved successfully from DB (not found in Redis).",
            data={"queue_length": len(email_list), "emails": email_list}
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

    redis_email_queue_key = f"email_queue:{user.uid}"     #this hash value will act as a pointer to the email queue for each user

    email_dict = email.model_dump()
    email_dict["uid"] = user_id
    email_dict["is_sent"] = False
    email_dict["send_at"] = datetime.utcnow().isoformat()

    new_email = Email(**email_dict)

    db_connection.add(new_email)
    db_connection.commit()

    email_dict["eid"] = new_email.eid

    redis_connection.rpush(redis_email_queue_key, json.dumps(email_dict))
    redis_connection.expire(redis_email_queue_key, 90*60)

    return ResponseSchema(
        success=True,
        status_code=200,
        message="Email added to the queue successfully.",
        data={"queue_length": redis_connection.llen(redis_email_queue_key)}
    )