from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.certificate import CertificateIssueRequest, CertificateResponse
from src.app.services.certificate_service import CertificateService

router = APIRouter(prefix="/certificates", tags=["Osvědčení a Certifikáty (Certificates)"])

@router.post("/issue", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
def issue_certificate(req: CertificateIssueRequest, db: Session = Depends(get_db)):
    return CertificateService.issue_certificate(db, req)

@router.get("/{certificate_number}", response_model=CertificateResponse)
def get_certificate(certificate_number: str, db: Session = Depends(get_db)):
    return CertificateService.get_by_number(db, certificate_number)
