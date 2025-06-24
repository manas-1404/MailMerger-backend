from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

import base64
from email.message import EmailMessage
import google.auth
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

from app.models import User, UserToken, Email
from app.pydantic_schemas.email_pydantic import EmailSchema
from app.db.dbConnection import get_db_session
from app.auth.dependency_auth import authenticate_request
from app.pydantic_schemas.response_pydantic import ResponseSchema
from app.utils.config import settings

email_router = APIRouter(
    prefix="/api/email",
    tags=["Email"]
)

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


def gmail_send_message(email_object: EmailSchema, google_access_token: str, from_email: str):
    """Create and send an email message
    Print the returned message id
    Returns: Message object, including message id

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """

    user_credentials = Credentials(token=google_access_token)

    try:
        service = build("gmail", "v1", credentials=user_credentials)
        message = EmailMessage()

        message.set_content(email_object.body)

        message["To"] = email_object.to_email
        message["From"] = from_email
        message["Subject"] = email_object.subject

        if email_object.cc_email:
            message["Cc"] = email_object.cc_email

        if email_object.bcc_email:
            message["Bcc"] = email_object.bcc_email

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



@email_router.post("/send-gmail-now")
def send_gmail_now(email_object: EmailSchema, jwt_payload: dict[str] = Depends(authenticate_request), db_connection: Session = Depends(get_db_session)):
    """
    Endpoint to send an email using Gmail API.
    """
    user_id = jwt_payload.get("sub")

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
            data={"redirect_url": "http://localhost:8000/api/oauth/gmail-authorize"}
        )

    gmail_access_token = user_token.access_token

    if user_token.expires_at < datetime.utcnow():
        gmail_access_token, gmail_access_token_expiry = refresh_google_access_token(user_token)

        user_token.access_token = gmail_access_token
        user_token.expires_at = gmail_access_token_expiry

        db_connection.flush()

    sent_message = gmail_send_message(
        google_access_token=gmail_access_token,
        from_email=user.email,
        email_object=email_object
    )

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


