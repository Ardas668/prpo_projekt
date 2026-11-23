from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.term import TermCreate, TermResponse
from src.app.services.term_service import TermService

router = APIRouter(prefix="/terms", tags=["Termíny (Terms)"])

@router.get("", response_model=list[TermResponse])
def get_terms(db: Session = Depends(get_db)):
    return TermService.get_all(db)

@router.post("", response_model=TermResponse, status_code=status.HTTP_201_CREATED)
def create_term(term_in: TermCreate, db: Session = Depends(get_db)):
    return TermService.create(db, term_in)

@router.get("/{term_id}", response_model=TermResponse)
def get_term(term_id: int, db: Session = Depends(get_db)):
    return TermService.get_term_response(db, term_id)
