from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.app.core.database import Base

class TermLecturer(Base):
    __tablename__ = "term_lecturers"

    term_id = Column(Integer, ForeignKey("terms.id", ondelete="CASCADE"), primary_key=True)
    lecturer_id = Column(Integer, ForeignKey("lecturers.id", ondelete="CASCADE"), primary_key=True)
    taught_hours = Column(Integer, default=0, nullable=False)

    term = relationship("Term", back_populates="term_lecturers")
    lecturer = relationship("Lecturer", back_populates="term_assignments")
