from pydantic import BaseModel
from datetime import date

class TermOccupancyReport(BaseModel):
    term_id: int
    course_name: str
    date_from: date
    date_to: date
    capacity: int
    confirmed_count: int
    waiting_count: int
    occupancy_percentage: float

class LecturerHoursReport(BaseModel):
    lecturer_id: int
    lecturer_name: str
    total_hours_taught: int
    terms_count: int

class MultiCourseStudentReport(BaseModel):
    student_id: int
    student_name: str
    email: str
    year: int
    courses_count: int
    courses: list[str]
