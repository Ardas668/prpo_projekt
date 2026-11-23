from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.models.lecturer import Lecturer
from src.app.schemas.lecturer import LecturerCreate, LecturerResponse

router = APIRouter(prefix="/lecturers", tags=["Lektoři (Lecturers)"])

@router.get("", response_model=list[LecturerResponse])
def get_lecturers(db: Session = Depends(get_db)):
    return db.query(Lecturer).all()

@router.post("", response_model=LecturerResponse, status_code=status.HTTP_201_CREATED)
def create_lecturer(lecturer_in: LecturerCreate, db: Session = Depends(get_db)):
    lecturer = Lecturer(**lecturer_in.model_dump())
    db.add(lecturer)
    db.commit()
    db.refresh(lecturer)
    return lecturer
