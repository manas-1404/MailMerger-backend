from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.routes.service_routes import send_gmail_service
from app.pydantic_schemas.email_pydantic import EmailSchema
from app.db.dbConnection import get_db_session
from app.auth.dependency_auth import authenticate_request

email_router = APIRouter(
    prefix="/api/email",
    tags=["Email"]
)


@email_router.post("/send-gmail-now")
def send_gmail_now_wrapper(email_object: EmailSchema, jwt_payload: dict[str] = Depends(authenticate_request), db_connection: Session = Depends(get_db_session)):
    """
    Endpoint to send an email using Gmail API.
    """

    return send_gmail_service(email_object=email_object, jwt_payload=jwt_payload, db_connection=db_connection)

