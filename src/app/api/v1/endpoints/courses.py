from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.course import CourseCreate, CourseResponse
from src.app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["Kurzy (Courses)"])

@router.get("", response_model=list[CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    return CourseService.get_all(db)

@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course_in: CourseCreate, db: Session = Depends(get_db)):
    return CourseService.create(db, course_in)

@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = CourseService.get_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kurz nenalezen.")
    return course
