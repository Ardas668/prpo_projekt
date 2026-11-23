from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from src.app.core.database import get_db
from src.app.schemas.report import TermOccupancyReport, LecturerHoursReport, MultiCourseStudentReport
from src.app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Přehledy a Statistiky (Reports)"])

@router.get("/occupancy", response_model=list[TermOccupancyReport])
def get_occupancy_report(db: Session = Depends(get_db)):
    return ReportService.get_term_occupancy(db)

@router.get("/lecturer-hours", response_model=list[LecturerHoursReport])
def get_lecturer_hours_report(db: Session = Depends(get_db)):
    return ReportService.get_lecturer_hours(db)

@router.get("/multi-course-students", response_model=list[MultiCourseStudentReport])
def get_multi_course_students_report(
    year: int = Query(default=datetime.now().year, description="Kalendářní rok"),
    db: Session = Depends(get_db)
):
    return ReportService.get_multi_course_students(db, year)
