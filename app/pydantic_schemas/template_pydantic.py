from typing import Optional

from pydantic import BaseModel

class TemplateSchema(BaseModel):
    template_id: Optional[int] = None
    uid: Optional[int] = None
    t_body: str
    t_key: str
