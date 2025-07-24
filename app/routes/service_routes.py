import os.path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime

import base64
from email.message import EmailMessage
import google.auth
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

from app.db.dbConnection import get_db_session
from app.models import User, UserToken, Email
from app.pydantic_schemas.email_pydantic import EmailSchema
from app.pydantic_schemas.response_pydantic import ResponseSchema
from app.services.storage_service import get_file_from_storage
from app.utils.config import settings


def refresh_google_access_token(user_token: UserToken):
    creds = Credentials(
        token=user_token.access_token,
        refresh_token=user_token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET
    )

    creds.refresh(Request())

    return creds.token, creds.expiry


def gmail_send_message(email_object: EmailSchema, google_access_token: str, from_email: str, user_token: UserToken, db_connection: Session, file_attachment_location: str = None):
    """Create and send an email message
    Print the returned message id
    Returns: Message object, including message id

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """

    if user_token.expires_at < datetime.utcnow():
        gmail_access_token, gmail_access_token_expiry = refresh_google_access_token(user_token)

        user_token.access_token = gmail_access_token
        user_token.expires_at = gmail_access_token_expiry

        db_connection.commit()

        google_access_token = user_token.access_token


    user_credentials = Credentials(token=google_access_token)

    try:
        service = build("gmail", "v1", credentials=user_credentials)
        message = EmailMessage()

        message.set_content(email_object.body, subtype="html", charset="utf-8")

        message["To"] = email_object.to_email
        message["From"] = from_email
        message["Subject"] = email_object.subject

        if email_object.cc_email:
            message["Cc"] = email_object.cc_email

        if email_object.bcc_email:
            message["Bcc"] = email_object.bcc_email

        if file_attachment_location is not None and os.path.exists(file_attachment_location):
            with open(file_attachment_location, "rb") as attachment_file:
                attachment_file_bytes = attachment_file.read()

            username = os.path.basename(file_attachment_location).replace(".pdf", "_resume.pdf").split("_", 1)

            filename_in_email = username[1]


            message.add_attachment(
                attachment_file_bytes,
                maintype="application", #for sending pdf files its maintype is application
                subtype="pdf",          #for sending pdf files only for now
                filename=filename_in_email
            )

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}

        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_message = None

    return send_message



def send_gmail_service(email_object: EmailSchema, user_id: str, db_connection: Session):
    """
    This is a wrapper for the Gmail service. Here we will check if the user has authorized Gmail access and then call the gmail service method to send the email.
    """

    user = db_connection.query(User).filter(User.uid == user_id).first()
    user_token = db_connection.query(UserToken).filter(UserToken.uid == user_id).first()

    if not user:
        return ResponseSchema(
            success=False,
            status_code=404,
            message="User not found.",
            data={}
        )

    # case where the user login through email and password, but never gives access to their gmail permissions
    if not user_token:
        return ResponseSchema(
            success=False,
            status_code=401,
            message="Gmail not authorized.",
            data={"redirect_url": "http://localhost:8000/api/oauth/gmail-authorize?purpose=authorize"}
        )

    gmail_access_token = user_token.access_token

    #the access token is expired, we need to refresh it
    if user_token.expires_at < datetime.utcnow():
        gmail_access_token, gmail_access_token_expiry = refresh_google_access_token(user_token)

        user_token.access_token = gmail_access_token
        user_token.expires_at = gmail_access_token_expiry

        db_connection.flush()

    resume_path_on_disk = None

    #user wants to include resume also in the email
    if email_object.include_resume:

        #checking if the user has a resume on file
        if not user.resume:
            raise HTTPException(
                status_code=400,
                detail="User does not have a resume uploaded."
            )

        resume_path_on_disk = get_file_from_storage(object_url=user.resume)

        if resume_path_on_disk == "download_failed":
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve resume from cloud storage."
            )

    sent_message = gmail_send_message(
        google_access_token=gmail_access_token,
        from_email=user.email,
        email_object=email_object,
        user_token=user_token,
        db_connection=db_connection,
        file_attachment_location=resume_path_on_disk
    )

    #remove the file from the disk once the email is sent
    if email_object.include_resume and resume_path_on_disk != "download_failed" and os.path.exists(resume_path_on_disk):
        os.remove(resume_path_on_disk)

    if sent_message:

        sent_email = Email(
            uid=user_id,
            google_message_id=sent_message['id'],
            subject=email_object.subject,
            body=email_object.body,
            is_sent=True,
            to_email=email_object.to_email,
            cc_email=email_object.cc_email,
            bcc_email=email_object.bcc_email,
            send_at=datetime.utcnow()
        )

        db_connection.add(sent_email)

        db_connection.commit()

        return ResponseSchema(
            status_code=201,
            success=True,
            message="Template added successfully.",
            data={"email_id": sent_email.eid}
        )

    else:
        failed_email = Email(
            uid=user_id,
            subject=email_object.subject,
            body=email_object.body,
            is_sent=False,
            to_email=email_object.to_email,
            cc_email=email_object.cc_email,
            bcc_email=email_object.bcc_email
        )

        db_connection.add(failed_email)
        db_connection.commit()

        return ResponseSchema(
            status_code=500,
            success=False,
            message="Failed to send email.",
            data={"email_id": failed_email.eid}
        )


