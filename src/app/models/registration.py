from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
from src.app.core.database import Base
from src.app.models.enums import RegistrationStatus

class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    term_id = Column(Integer, ForeignKey("terms.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(RegistrationStatus), nullable=False, default=RegistrationStatus.CONFIRMED, index=True)
    queue_position = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    admin_override = Column(Boolean, default=False, nullable=False)
    admin_override_reason = Column(String(255), nullable=True)

    student = relationship("Student", back_populates="registrations")
    term = relationship("Term", back_populates="registrations")
    attendances = relationship("Attendance", back_populates="registration", cascade="all, delete-orphan")
    certificate = relationship("Certificate", back_populates="registration", uselist=False, cascade="all, delete-orphan")
