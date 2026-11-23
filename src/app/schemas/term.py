from pydantic import BaseModel, Field, ConfigDict
from datetime import date

class TermLecturerAssign(BaseModel):
    lecturer_id: int
    taught_hours: int = Field(..., ge=0)

class TermLecturerResponse(BaseModel):
    lecturer_id: int
    taught_hours: int
    lecturer_name: str | None = None
    model_config = ConfigDict(from_attributes=True)

class TermBase(BaseModel):
    course_id: int
    date_from: date
    date_to: date
    location: str = Field(..., max_length=150)
    classroom: str = Field(..., max_length=50)
    capacity: int = Field(..., gt=0)

class TermCreate(TermBase):
    lecturers: list[TermLecturerAssign] = []

class TermResponse(TermBase):
    id: int
    confirmed_students_count: int = 0
    waiting_list_count: int = 0
    is_full: bool = False
    lecturers: list[TermLecturerResponse] = []
    model_config = ConfigDict(from_attributes=True)
