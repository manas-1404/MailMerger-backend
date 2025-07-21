from passlib.context import CryptContext
import time
import uuid
import json
import re
from pydantic import BaseModel
from typing import Any, Dict, Union

crypt_context = CryptContext(schemes=["bcrypt"])

def encrypt_string(plain_string: str) -> str:
    """Encrypts a plain string using bcrypt."""
    return crypt_context.hash(plain_string)

def verify_string(plain_string: str, hashed_string: str) -> bool:
    """Verifies a plain string against a hashed string."""
    return crypt_context.verify(plain_string, hashed_string)

def credentials_to_dict(credentials):
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "granted_scopes": credentials.scopes,
        "expiry": str(credentials.expiry)
    }

def generate_eid(user_id: str) -> str:
    timestamp = int(time.time() * 1000)
    random_suffix = uuid.uuid4().hex[:8]
    return f"{user_id}_{timestamp}_{random_suffix}"

def serialize_for_redis(data: Any) -> str:
    """
    Serialize any Python object to a JSON string suitable for storing in Redis.
    Supports dicts, lists, primitives, and Pydantic models.
    """
    if data is None:
        return "null"

    if isinstance(data, str):
        return data

    if isinstance(data, (int, float, bool)):
        return json.dumps(data)

    if isinstance(data, BaseModel):
        return data.model_dump_json()

    if isinstance(data, (list, dict)):
        return json.dumps(data)

    try:
        #if everything fails, then the data is an custom object, so convert it to a dict and return it
        return json.dumps(data.__dict__)
    except (AttributeError, TypeError):
        #data is weird and cannot be serialized, so we return it as a string
        return str(data)

def deserialize_from_redis(data: Union[bytes, str, Dict[bytes, bytes]]) -> Any:
    """
    Deserialize Redis-stored data into proper Python types.
    """
    #handle the returns from redis alls methods
    if isinstance(data, dict):
        return {
            key.decode() if isinstance(key, bytes) else str(key):
            json.loads(value.decode() if isinstance(value, bytes) else value)
            for key, value in data.items()
        }

    #handle the returns from regular redis get methods
    elif isinstance(data, (bytes, str)):
        try:
            string_data = data.decode() if isinstance(data, bytes) else data
            return json.loads(string_data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return string_data  # Fallback to plain string

    #raise an error if the data is not a supported type
    else:
        assert False, "Unsupported data type for deserialization"
        return data

def sanitize_filename_base(name: str) -> str:
    """
    Replace any character that is not a-z, A-Z, 0-9, underscore with '_'.
    This removes spaces, dots, accents, and special characters.
    """
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)
