from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.app.models.certificate import Certificate
from src.app.models.registration import Registration
from src.app.models.enums import RegistrationStatus
from src.app.services.attendance_service import AttendanceService
from src.app.schemas.certificate import CertificateIssueRequest, CertificateResponse

class CertificateService:
    @staticmethod
    def issue_certificate(db: Session, req: CertificateIssueRequest) -> CertificateResponse:
        reg = db.query(Registration).filter(Registration.id == req.registration_id).first()
        if not reg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Přihláška nenalezena.")

        if reg.status != RegistrationStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Osvědčení lze vystavit pouze řádně přihlášenému účastníkovi."
            )

        # Pravidlo neměnnosti: již vydané osvědčení nelze měnit ani přegenerovat
        existing = db.query(Certificate).filter(Certificate.registration_id == reg.id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Osvědčení pro tuto přihlášku již bylo vystaveno (číslo: {existing.certificate_number}) a je neměnné."
            )

        # Pravidlo 1 z ADR-003: Docházka >= 70 % A souhlas lektora
        if not req.lecturer_approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kurz nelze zakončit bez schválení lektorem."
            )

        att_summary = AttendanceService.get_summary(db, reg.id)
        if att_summary.total_days > 0 and not att_summary.meets_minimum_requirement:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student nesplnil minimální 70% docházku (současný stav: {att_summary.attendance_percentage}%)."
            )

        year = reg.term.date_from.year if reg.term else datetime.now().year
        cert_number = f"TRU-{year}-{reg.id:04d}"

        cert = Certificate(
            registration_id=reg.id,
            certificate_number=cert_number,
            issued_at=datetime.now(timezone.utc)
        )
        db.add(cert)
        db.commit()
        db.refresh(cert)

        student_name = f"{reg.student.first_name} {reg.student.last_name}" if reg.student else None
        course_name = reg.term.course.name if reg.term and reg.term.course else None

        return CertificateResponse(
            id=cert.id,
            registration_id=cert.registration_id,
            certificate_number=cert.certificate_number,
            issued_at=cert.issued_at,
            student_name=student_name,
            course_name=course_name
        )

    @staticmethod
    def get_by_number(db: Session, cert_number: str) -> CertificateResponse:
        cert = db.query(Certificate).filter(Certificate.certificate_number == cert_number).first()
        if not cert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Osvědčení nenalezeno.")

        reg = cert.registration
        student_name = f"{reg.student.first_name} {reg.student.last_name}" if reg and reg.student else None
        course_name = reg.term.course.name if reg and reg.term and reg.term.course else None

        return CertificateResponse(
            id=cert.id,
            registration_id=cert.registration_id,
            certificate_number=cert.certificate_number,
            issued_at=cert.issued_at,
            student_name=student_name,
            course_name=course_name
        )
