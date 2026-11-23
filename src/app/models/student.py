from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.app.core.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)

    registrations = relationship("Registration", back_populates="student", cascade="all, delete-orphan")
