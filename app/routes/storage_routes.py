import os.path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependency_auth import authenticate_request
from app.db.dbConnection import get_db_session
from app.models import User
from app.pydantic_schemas.response_pydantic import ResponseSchema
from app.services.storage_service import upload_file_to_storage
from app.utils.utils import sanitize_filename_base

storage_router = APIRouter(
    prefix="/api/storage",
    tags=["Storage"]
)

@storage_router.post("/upload-file")
def upload_file(uploaded_file: UploadFile = File(...), filecontent: str = "resume", jwt_payload: dict = Depends(authenticate_request), db_connection: Session = Depends(get_db_session)):
    """
    Endpoint to upload a file to the storage service.
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

    if uploaded_file.content_type != "application/pdf":
        return ResponseSchema(
            success=False,
            status_code=400,
            message="Only PDF files are allowed.",
            data={}
        )

    file_bytes = uploaded_file.file.read()

    if len(file_bytes) > 5*1024*1024:
        return ResponseSchema(
            success=False,
            status_code=400,
            message="File size exceeds the maximum limit of 5MB.",
            data={}
        )

    temp_storage_dir = "temp"
    os.makedirs(temp_storage_dir, exist_ok=True)

    new_file_name = f"{user_id}_{sanitize_filename_base(name=user.name)}.pdf"

    temp_file_path = os.path.join(temp_storage_dir, new_file_name)

    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(file_bytes)

    try:

        file_url = upload_file_to_storage(file_path=temp_file_path)

        print(f"File URL: {file_url}")

        if file_url != "upload_failed":

            user.resume = file_url

            db_connection.commit()

            os.remove(temp_file_path)

            return ResponseSchema(
                success=True,
                status_code=200,
                message="File uploaded successfully.",
                data={}
            )

        os.remove(temp_file_path)

        return ResponseSchema(
            success=False,
            status_code=500,
            message="File upload failed.",
            data={}
        )

    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return ResponseSchema(
            success=False,
            status_code=500,
            message=f"An error occurred while uploading the file",
            data={"Error": str(e)}
        )
