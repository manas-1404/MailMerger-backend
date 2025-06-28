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

    try:

        user = db_connection.query(User).options(joinedload(User.user_tokens)).filter(User.uid == user_id).first()

        while True:

            email_json = redis_connection.lpop(redis_queue_key)
            if email_json is None:
                break

            email_data = json.loads(email_json)

            email_object = EmailSchema.model_validate(email_data)

            service_response = gmail_send_message(email_object=email_object, google_access_token=user.user_tokens[0].access_token, from_email=user.email)

            if email_object.eid:
                #update the status of the email in db
                db_connection.query(Email).filter(Email.eid == email_object.eid).update({
                    Email.is_sent: True if service_response else False,
                    Email.google_message_id: service_response.get('id') if service_response else None,
                    Email.send_at: datetime.utcnow() if service_response else None
                })

            else:
                #this is a new email directly from redis

                new_email = Email(
                    uid=user_id,
                    google_message_id=service_response.get('id') if service_response else None,
                    subject=email_object.subject,
                    body=email_object.body,
                    is_sent=True if service_response else False,
                    to_email=email_object.to_email,
                    cc_email=email_object.cc_email,
                    bcc_email=email_object.bcc_email,
                    send_at=datetime.utcnow() if service_response else None
                )

                db_connection.add(new_email)

        db_connection.commit()

    finally:
        db_gen.close()