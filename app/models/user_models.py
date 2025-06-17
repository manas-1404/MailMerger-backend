from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.models.base_model import Base

class User(Base):

    __tablename__ = 'users'

    uid = Column(Integer, primary_key=True, autoincrement=True, unique=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    resume = Column(String, nullable=True)
    cover_letter = Column(String, nullable=True)

    emails = relationship('Email', back_populates='user', cascade='all, delete', lazy='select')
    templates = relationship('Template', back_populates='user', cascade='all, delete', lazy='select')
    user_tokens = relationship('UserToken', back_populates='user', cascade='all, delete', lazy='select')