from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.app.models.attendance import Attendance
from src.app.models.registration import Registration
from src.app.models.enums import RegistrationStatus
from src.app.schemas.attendance import AttendanceBulkCreate, AttendanceResponse, AttendanceSummaryResponse

class AttendanceService:
    @staticmethod
    def log_attendance(db: Session, data: AttendanceBulkCreate) -> list[AttendanceResponse]:
        reg = db.query(Registration).filter(Registration.id == data.registration_id).first()
        if not reg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Přihláška nenalezena.")

        if reg.status != RegistrationStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Docházku lze evidovat pouze u potvrzených (CONFIRMED) přihlášek."
            )

        responses = []
        for rec in data.records:
            existing = db.query(Attendance).filter(
                Attendance.registration_id == reg.id,
                Attendance.date == rec.date
            ).first()

            if existing:
                existing.is_present = rec.is_present
                existing.note = rec.note
                att_obj = existing
            else:
                att_obj = Attendance(
                    registration_id=reg.id,
                    date=rec.date,
                    is_present=rec.is_present,
                    note=rec.note
                )
                db.add(att_obj)

            db.flush()
            responses.append(AttendanceResponse.model_validate(att_obj))

        db.commit()
        return responses

    @staticmethod
    def get_summary(db: Session, registration_id: int) -> AttendanceSummaryResponse:
        reg = db.query(Registration).filter(Registration.id == registration_id).first()
        if not reg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Přihláška nenalezena.")

        total = db.query(Attendance).filter(Attendance.registration_id == registration_id).count()
        attended = db.query(Attendance).filter(
            Attendance.registration_id == registration_id,
            Attendance.is_present == True
        ).count()

        pct = (attended / total * 100.0) if total > 0 else 0.0

        return AttendanceSummaryResponse(
            registration_id=reg.id,
            student_name=f"{reg.student.first_name} {reg.student.last_name}" if reg.student else "Neznámý",
            total_days=total,
            attended_days=attended,
            attendance_percentage=round(pct, 2),
            meets_minimum_requirement=(pct >= 70.0)
        )
