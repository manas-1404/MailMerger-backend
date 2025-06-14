from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base_model import Base

class Template(Base):

    __tablename__ = 'templates'

    template_id = Column(Integer, primary_key=True, autoincrement=True, unique=True, index=True)
    uid = Column(Integer, ForeignKey('users.uid'), nullable=False)
    t_body = Column(String, nullable=False)
    t_key = Column(String, nullable=False)

    # Assuming a relationship with User model exists
    user = relationship('User', back_populates='templates')