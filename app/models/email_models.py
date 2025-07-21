from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base_model import Base


class Email(Base):

    __tablename__ = 'emails'

    eid = Column(Integer, primary_key=True, autoincrement=True, unique=True, index=True)
    uid = Column(Integer, ForeignKey('users.uid'), nullable=False)
    google_message_id = Column(String, nullable=True, unique=True)
    subject = Column(String, nullable=False)
    body = Column(String, nullable=False)
    is_sent = Column(Boolean, default=False)
    to_email = Column(String, nullable=False)
    cc_email = Column(String, nullable=True)
    bcc_email = Column(String, nullable=True)
    send_at = Column(DateTime, nullable=False)
    include_resume = Column(Boolean, default=False)

    user = relationship('User', back_populates='emails')