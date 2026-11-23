from src.app.core.database import Base
from src.app.models.enums import RegistrationStatus
from src.app.models.course import Course
from src.app.models.term import Term
from src.app.models.lecturer import Lecturer
from src.app.models.term_lecturer import TermLecturer
from src.app.models.student import Student
from src.app.models.registration import Registration
from src.app.models.attendance import Attendance
from src.app.models.certificate import Certificate

__all__ = [
    "Base",
    "RegistrationStatus",
    "Course",
    "Term",
    "Lecturer",
    "TermLecturer",
    "Student",
    "Registration",
    "Attendance",
    "Certificate",
]
