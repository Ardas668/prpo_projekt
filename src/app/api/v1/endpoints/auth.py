from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.app.core.config import settings
from src.app.core.database import get_db
from src.app.models.lecturer import Lecturer
from src.app.models.student import Student
from src.app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Přihlášení (Auth)"])


@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    email_norm = credentials.email.strip().lower()
    password = credentials.password

    # 1. Administrátor (přihlašovací údaje z .env)
    if email_norm == settings.ADMIN_EMAIL.strip().lower():
        if password == settings.ADMIN_PASSWORD:
            return LoginResponse(
                role="admin",
                user_id=None,
                full_name="Ing. Lucie Bartošová",
                email=settings.ADMIN_EMAIL,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neplatný e-mail nebo heslo.",
        )

    # 2. Lektor (e-mail z databáze + heslo pro lektory z .env)
    lecturer = (
        db.query(Lecturer)
        .filter(func.lower(Lecturer.email) == email_norm)
        .first()
    )
    if lecturer:
        if password == settings.LECTURER_DEMO_PASSWORD:
            return LoginResponse(
                role="lecturer",
                user_id=lecturer.id,
                full_name=f"{lecturer.first_name} {lecturer.last_name}",
                email=lecturer.email,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neplatný e-mail nebo heslo.",
        )

    # 3. Student (e-mail z databáze + heslo pro studenty z .env)
    student = (
        db.query(Student)
        .filter(func.lower(Student.email) == email_norm)
        .first()
    )
    if student:
        if password == settings.STUDENT_DEMO_PASSWORD:
            return LoginResponse(
                role="student",
                user_id=student.id,
                full_name=f"{student.first_name} {student.last_name}",
                email=student.email,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neplatný e-mail nebo heslo.",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Účet s tímto e-mailem nebyl nalezen.",
    )
