from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.registration import RegistrationCreate, RegistrationResponse, RegistrationCancelResponse
from src.app.services.registration_service import RegistrationService

router = APIRouter(prefix="/registrations", tags=["Přihlášky a Pořadník (Registrations & Queue)"])

@router.post("", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_student(reg_in: RegistrationCreate, db: Session = Depends(get_db)):
    return RegistrationService.register_student(db, reg_in)

@router.post("/{registration_id}/cancel", response_model=RegistrationCancelResponse)
def cancel_registration(registration_id: int, db: Session = Depends(get_db)):
    return RegistrationService.cancel_registration(db, registration_id)

@router.get("/term/{term_id}", response_model=list[RegistrationResponse])
def get_term_registrations(term_id: int, db: Session = Depends(get_db)):
    regs = RegistrationService.get_by_term(db, term_id)
    return [RegistrationService._build_response(r) for r in regs]
