from typing import Optional

from pydantic import BaseModel

class EmailSchema(BaseModel):
    eid: Optional[int] = None
    uid: Optional[int] = None
    subject: str
    body: str
    is_sent: bool = False
    to_email: str
    cc_email: Optional[str] = None
    bcc_email: Optional[str] = None
    send_at: Optional[str] = None