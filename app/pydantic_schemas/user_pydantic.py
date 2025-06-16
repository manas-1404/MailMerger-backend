from typing import Optional

from pydantic import BaseModel

#i will use this schema only to receive data from the frontend
class UserSchema(BaseModel):
    uid: Optional[int] = None
    name: str
    email: str
    password: str
    resume: Optional[str] = None
    cover_letter: Optional[str] = None

