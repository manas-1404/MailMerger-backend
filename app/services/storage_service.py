import httpx
import os
from app.utils.config import settings

def get_file_from_storage(object_url: str) -> str:
    """
    Download a file from a remote storage service.

    :param object_url: URL of the file to be downloaded.
    :return: Full path to the downloaded file if successful, False otherwise.
    """

    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE}"
    }

    try:
        response = httpx.get(url=object_url, headers=headers)

        if response.status_code == 200:
            filename = object_url.split("/")[-1]

            os.makedirs("downloads", exist_ok=True)
            file_path = os.path.join("downloads", filename)

            with open(file_path, "wb") as file:
                file.write(response.content)

            return file_path
        else:
            print(f"Failed to download file: {response.status_code}")
            return "download_failed"

    except httpx.RequestError as e:
        print(f"An error occurred while downloading the file: {e}")
        return "download_failed"


def upload_file_to_storage(file_path: str) -> str:
    """
    Upload a file to a remote storage service.

    :param file_path: Path to the file to be uploaded.
    :return: Full object url if upload was successful, False otherwise.
    """
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return False

    filename: str = os.path.basename(file_path)
    bucketName: str = "mailstorm-storage"
    wildcard: str = f"resume/{filename}"
    object_url: str = f"{settings.SUPABASE_S3_STORAGE_ENDPOINT}/object/{bucketName}/{wildcard}"

    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE}",
        "Content-Type": "application/pdf",
    }

    with open(file_path, "rb") as upload_file:
        upload_file_bytes = upload_file.read()

    try:
        response = httpx.post(url=object_url, headers=headers, content=upload_file_bytes)
        return object_url if response.status_code == 200 else "upload_failed"

    except httpx.RequestError as e:
        print(f"An error occurred while uploading the file: {e}")
        return "upload_failed"