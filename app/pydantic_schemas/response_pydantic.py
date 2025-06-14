from pydantic import BaseModel
from typing import Optional, Dict

class ResponseSchema(BaseModel):
    success: bool = True
    status_code: int
    message: Optional[str] = None
    data: Optional[Dict] = None
