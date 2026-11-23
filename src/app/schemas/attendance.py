from pydantic import BaseModel, ConfigDict
from datetime import date

class AttendanceRecord(BaseModel):
    date: date
    is_present: bool = True
    note: str | None = None

class AttendanceBulkCreate(BaseModel):
    registration_id: int
    records: list[AttendanceRecord]

class AttendanceResponse(BaseModel):
    id: int
    registration_id: int
    date: date
    is_present: bool
    note: str | None = None
    model_config = ConfigDict(from_attributes=True)

class AttendanceSummaryResponse(BaseModel):
    registration_id: int
    student_name: str
    total_days: int
    attended_days: int
    attendance_percentage: float
    meets_minimum_requirement: bool  # >= 70 %
