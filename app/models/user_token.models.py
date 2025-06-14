from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base_model import Base

class UserToken(Base):

    __tablename__ = 'user_tokens'

    token_id = Column(Integer, primary_key=True, autoincrement=True, unique=True, index=True)
    uid = Column(Integer, ForeignKey('users.uid'), nullable=False)
    access_token = Column(String, nullable=False, unique=True)
    refresh_token = Column(String, nullable=False, unique=True)
    token_type = Column(String, nullable=False, default='gmail')
    expires_at = Column(DateTime, nullable=False)

    # Assuming a relationship with User model exists
    user = relationship('User', back_populates='user_tokens')