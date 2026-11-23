from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from src.app.core.database import Base

class Term(Base):
    __tablename__ = "terms"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    location = Column(String(150), nullable=False)
    classroom = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)

    course = relationship("Course", back_populates="terms")
    registrations = relationship("Registration", back_populates="term", cascade="all, delete-orphan")
    term_lecturers = relationship("TermLecturer", back_populates="term", cascade="all, delete-orphan")
