from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.attendance import AttendanceBulkCreate, AttendanceResponse, AttendanceSummaryResponse
from src.app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["Docházka (Attendance)"])

@router.post("", response_model=list[AttendanceResponse], status_code=status.HTTP_201_CREATED)
def record_attendance(data: AttendanceBulkCreate, db: Session = Depends(get_db)):
    return AttendanceService.log_attendance(db, data)

@router.get("/summary/{registration_id}", response_model=AttendanceSummaryResponse)
def get_attendance_summary(registration_id: int, db: Session = Depends(get_db)):
    return AttendanceService.get_summary(db, registration_id)
