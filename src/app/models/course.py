from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric
from sqlalchemy.orm import relationship
from src.app.core.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    annotation = Column(Text, nullable=True)
    hours_duration = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    is_accredited = Column(Boolean, default=False, nullable=False)

    terms = relationship("Term", back_populates="course", cascade="all, delete-orphan")
