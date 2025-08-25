import json
import os.path
from datetime import datetime
from typing import List

from redis.asyncio.client import Pipeline
from sqlalchemy import text
from sqlalchemy.orm import joinedload

from app.celery_worker import celery_app
from app.db.dbConnection import get_db_session
from app.db.redisConnection import get_redis_connection
from app.models import User, UserToken, Email
from app.pydantic_schemas.email_pydantic import EmailSchema
from app.routes.service_routes import gmail_send_message
from app.services.storage_service import get_file_from_storage


@celery_app.task(name="send_emails_from_user_queue")
async def send_emails_from_user_queue(user_id: str, email_ids: List[int]):
    """
    Celery task to send emails from the user's queue.
    This function will be called by the Celery worker.
    """

    db_gen = get_db_session()
    db_connection = next(db_gen)

    redis_connection = await get_redis_connection()

    redis_queue_key = f"email_queue:{user_id}"
    redis_failed_queue_key = f"failed_email_queue:{user_id}"

    updated_send_at_records = {}
    updated_google_message_id_records = {}
    new_db_records = []

    try:

        user = db_connection.query(User).options(joinedload(User.user_tokens)).filter(User.uid == user_id).first()

        email_queue = await redis_connection.lrange(redis_queue_key, 0, -1)

        redis_pipeline: Pipeline = redis_connection.pipeline()

        redis_pipeline.delete(redis_queue_key)

        resume_path_on_disk = None

        for email_json in email_queue:

            email_data = json.loads(email_json)

            if email_data.get("eid") not in email_ids:
                #If the email ID is not in the provided list, skip processing this email
                redis_pipeline.rpush(redis_queue_key, email_json)
                continue

            email_object = EmailSchema.model_validate(email_data)

            if email_object.include_resume:

                # checking if the user has a resume on file
                if not user.resume:
                    #if the user does not have a resume uploaded, we cannot proceed so skip this email
                    redis_pipeline.rpush(redis_failed_queue_key, email_json)
                    continue

                resume_path_on_disk = get_file_from_storage(object_url=user.resume) if resume_path_on_disk is None or resume_path_on_disk=="download_failed" else resume_path_on_disk

                if resume_path_on_disk == "download_failed":
                    #if the resume download failed, we cannot proceed so skip this email
                    redis_pipeline.rpush(redis_failed_queue_key, email_json)
                    continue

            try:
                service_response = gmail_send_message(email_object=email_object,
                                                      google_access_token=user.user_tokens[0].access_token,
                                                      from_email=user.email,
                                                      user_token=user.user_tokens[0],
                                                      db_connection=db_connection,
                                                      file_attachment_location=resume_path_on_disk if email_object.include_resume else None)
            except Exception as e:
                print(f"Error sending email: {e}")
                email_data["retry_count"] = email_data.get("retry_count", 0) + 1
                email_data["error"] = str(e)
                redis_pipeline.rpush(redis_failed_queue_key, json.dumps(email_data))

            if service_response:
                if email_object.eid:
                    #update the status of the email in db
                    updated_send_at_records[email_object.eid] = datetime.utcnow()
                    updated_google_message_id_records[email_object.eid] = service_response.get('id')

                    print("All updated records: ", updated_send_at_records)
                    print("-"*50)
                    print("All updated google message id records: ", updated_google_message_id_records)

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
                    new_db_records.append(new_email)

            else:
                email_data["retry_count"] = email_data.get("retry_count", 0) + 1
                redis_pipeline.rpush(redis_failed_queue_key, json.dumps(email_data))

        redis_pipeline.expire(redis_queue_key, 90 * 60)
        redis_pipeline.expire(redis_failed_queue_key, 90 * 60)
        await redis_pipeline.execute()

        if resume_path_on_disk and resume_path_on_disk != "download_failed" and os.path.exists(resume_path_on_disk):
            os.remove(resume_path_on_disk)

        if new_db_records:
            db_connection.bulk_save_objects(new_db_records)

        if updated_send_at_records and updated_google_message_id_records:

            eids = list(updated_send_at_records.keys())

            send_at_case = "CASE\n"
            google_message_id_case = "CASE\n"

            for eid in eids:
                send_at = updated_send_at_records[eid]
                google_message_id = updated_google_message_id_records[eid]
                send_at_case += f"  WHEN eid = {eid} THEN '{send_at.isoformat()}'::timestamp\n"
                google_message_id_case += f"  WHEN eid = {eid} THEN '{google_message_id}'\n"

            send_at_case += "END"
            google_message_id_case += "END"

            sql_query = f"""
                    UPDATE emails
                    SET 
                        is_sent = TRUE,
                        send_at = {send_at_case},
                        google_message_id = {google_message_id_case}
                    WHERE eid IN ({','.join(map(str, eids))});
                """

            db_connection.execute(text(sql_query))

        db_connection.commit()

    finally:
        db_gen.close()


@celery_app.task(name="retry_failed_emails")
async def retry_failed_emails(user_id: str):
    db_gen = get_db_session()
    db = next(db_gen)
    redis_gen = await get_redis_connection()
    redis = redis_gen

    failed_key = f"failed_email_queue:{user_id}"
    dead_key = f"dead_email_queue:{user_id}"

    try:
        user = db.query(User).options(joinedload(User.user_tokens)).filter(User.uid == user_id).first()
        if not user or not user.user_tokens:
            return

        while True:
            email_json = await redis.lpop(failed_key)
            if email_json is None:
                break

            email_data = json.loads(email_json)
            retry_count = email_data.get("retry_count", 0)

            email_obj = EmailSchema.model_validate(email_data)

            response = gmail_send_message(email_object=email_obj, google_access_token=user.user_tokens[0].access_token, from_email=user.email, user_token=user.user_tokens[0], db_connection=db)

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
                    await redis.rpush(dead_key, json.dumps(email_data))
                else:
                    await redis.rpush(failed_key, json.dumps(email_data))

        db.commit()

    finally:
        db_gen.close()
        await redis_gen.close()