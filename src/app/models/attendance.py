from sqlalchemy import Column, Integer, Date, Boolean, String, ForeignKey
from sqlalchemy.orm import relationship
from src.app.core.database import Base

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    registration_id = Column(Integer, ForeignKey("registrations.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    is_present = Column(Boolean, default=False, nullable=False)
    note = Column(String(255), nullable=True)

    registration = relationship("Registration", back_populates="attendances")
