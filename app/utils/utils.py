from passlib.context import CryptContext

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
