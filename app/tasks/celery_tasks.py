import json
from datetime import datetime

from sqlalchemy.orm import joinedload

from app.celery_worker import celery_app
from app.db.dbConnection import get_db_session
from app.db.redisConnection import get_redis_connection
from app.models import User, UserToken, Email
from app.pydantic_schemas.email_pydantic import EmailSchema
from app.routes.service_routes import gmail_send_message


@celery_app.task(name="send_emails_from_user_queue")
def send_emails_from_user_queue(user_id: str):
    """
    Celery task to send emails from the user's queue.
    This function will be called by the Celery worker.
    """

    db_gen = get_db_session()
    db_connection = next(db_gen)
    redis_connection = next(get_redis_connection())

    redis_queue_key = f"email_queue:{user_id}"
    redis_failed_queue_key = f"failed_email_queue:{user_id}"

    try:

        user = db_connection.query(User).options(joinedload(User.user_tokens)).filter(User.uid == user_id).first()

        while True:

            email_json = redis_connection.lpop(redis_queue_key)
            if email_json is None:
                break

            email_data = json.loads(email_json)

            email_object = EmailSchema.model_validate(email_data)

            service_response = gmail_send_message(email_object=email_object, google_access_token=user.user_tokens[0].access_token, from_email=user.email)

            if service_response:
                if email_object.eid:
                    #update the status of the email in db
                    db_connection.query(Email).filter(Email.eid == email_object.eid).update({
                        Email.is_sent: True,
                        Email.google_message_id: service_response.get('id') ,
                        Email.send_at: datetime.utcnow()
                    })

                else:
                    #this is a new email directly from redis

                    new_email = Email(
                        uid=user_id,
                        google_message_id=service_response.get('id') ,
                        subject=email_object.subject,
                        body=email_object.body,
                        is_sent=True,
                        to_email=email_object.to_email,
                        cc_email=email_object.cc_email,
                        bcc_email=email_object.bcc_email,
                        send_at=datetime.utcnow()
                    )

                    db_connection.add(new_email)

            else:
                email_data["retry_count"] = email_data.get("retry_count", 0) + 1
                redis_connection.rpush(redis_failed_queue_key, json.dumps(email_data))

        db_connection.commit()

    finally:
        db_gen.close()


@celery_app.task(name="retry_failed_emails")
def retry_failed_emails(user_id: str):
    db_gen = get_db_session()
    db = next(db_gen)
    redis_gen = get_redis_connection()
    redis = next(redis_gen)

    failed_key = f"failed_email_queue:{user_id}"
    dead_key = f"dead_email_queue:{user_id}"

    try:
        user = db.query(User).options(joinedload(User.user_tokens)).filter(User.uid == user_id).first()
        if not user or not user.user_tokens:
            return

        while True:
            email_json = redis.lpop(failed_key)
            if email_json is None:
                break

            email_data = json.loads(email_json)
            retry_count = email_data.get("retry_count", 0)

            email_obj = EmailSchema.model_validate(email_data)

            response = gmail_send_message(email_object=email_obj, google_access_token=user.user_tokens[0].access_token, from_email=user.email)

            if response:
                # Mark as sent in DB
                if email_obj.eid:
                    db.query(Email).filter(Email.eid == email_obj.eid).update({
                        Email.is_sent: True,
                        Email.google_message_id: response.get("id"),
                        Email.send_at: datetime.utcnow()
                    })
                else:
                    db.add(Email(
                        uid=user_id,
                        google_message_id=response.get("id"),
                        subject=email_obj.subject,
                        body=email_obj.body,
                        is_sent=True,
                        to_email=email_obj.to_email,
                        cc_email=email_obj.cc_email,
                        bcc_email=email_obj.bcc_email,
                        send_at=datetime.utcnow()
                    ))
            else:
                retry_count += 1
                email_data["retry_count"] = retry_count

                if retry_count > 3:
                    redis.rpush(dead_key, json.dumps(email_data))
                else:
                    redis.rpush(failed_key, json.dumps(email_data))

        db.commit()

    finally:
        db_gen.close()
        redis_gen.close()