from pydantic import BaseModel
from typing import Optional, Any

class ErrorSchema(BaseModel):
    success: bool = False
    status_code: int
    message: str
    errors: Optional[str] = None
    data: Optional[Any] = None