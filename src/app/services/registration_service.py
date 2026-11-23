from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from src.app.models.registration import Registration
from src.app.models.term import Term
from src.app.models.student import Student
from src.app.models.enums import RegistrationStatus
from src.app.schemas.registration import RegistrationCreate, RegistrationResponse, RegistrationCancelResponse

class RegistrationService:
    @staticmethod
    def get_by_term(db: Session, term_id: int) -> list[Registration]:
        return db.query(Registration).filter(Registration.term_id == term_id).all()

    @staticmethod
    def register_student(db: Session, reg_in: RegistrationCreate) -> RegistrationResponse:
        student = db.query(Student).filter(Student.id == reg_in.student_id).first()
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student nenalezen.")

        term = db.query(Term).filter(Term.id == reg_in.term_id).first()
        if not term:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Termín kurzu nenalezen.")

        # Pravidlo 4: Přihlášení po zahájení termínu
        today = date.today()
        if term.date_from <= today and not reg_in.admin_override:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Termín již byl zahájen. Přihlášení je možné pouze se souhlasem administrátora (admin_override)."
            )

        # Pravidlo 3: Zákaz souběhu aktivních přihlášek na stejný kurz
        existing_active = (
            db.query(Registration)
            .join(Term, Registration.term_id == Term.id)
            .filter(
                Registration.student_id == student.id,
                Term.course_id == term.course_id,
                Registration.status.in_([RegistrationStatus.CONFIRMED, RegistrationStatus.WAITING_LIST])
            )
            .first()
        )
        if existing_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student již má aktivní přihlášku na tento kurz (termín ID {existing_active.term_id}, stav: {existing_active.status})."
            )

        # Počet aktuálně potvrzených účastníků
        confirmed_count = db.query(Registration).filter(
            Registration.term_id == term.id,
            Registration.status == RegistrationStatus.CONFIRMED
        ).count()

        # Pravidlo 1 & 2: Nepřekročení kapacity + FIFO pořadník
        if confirmed_count < term.capacity:
            new_reg = Registration(
                student_id=student.id,
                term_id=term.id,
                status=RegistrationStatus.CONFIRMED,
                queue_position=None,
                admin_override=reg_in.admin_override,
                admin_override_reason=reg_in.admin_override_reason
            )
        else:
            # Kapacita je plná -> zařazení do pořadníku (FIFO)
            max_pos = db.query(func.max(Registration.queue_position)).filter(
                Registration.term_id == term.id,
                Registration.status == RegistrationStatus.WAITING_LIST
            ).scalar() or 0

            new_reg = Registration(
                student_id=student.id,
                term_id=term.id,
                status=RegistrationStatus.WAITING_LIST,
                queue_position=max_pos + 1,
                admin_override=reg_in.admin_override,
                admin_override_reason=reg_in.admin_override_reason
            )

        db.add(new_reg)
        db.commit()
        db.refresh(new_reg)
        return RegistrationService._build_response(new_reg)

    @staticmethod
    def cancel_registration(db: Session, registration_id: int) -> RegistrationCancelResponse:
        reg = db.query(Registration).filter(Registration.id == registration_id).first()
        if not reg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Přihláška nenalezena.")

        if reg.status == RegistrationStatus.CANCELLED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Přihláška již byla zrušena.")

        old_status = reg.status
        old_queue_pos = reg.queue_position

        # Auditní uchování zrušené přihlášky (fyzicky se nemaže)
        reg.status = RegistrationStatus.CANCELLED
        reg.cancelled_at = datetime.now(timezone.utc)
        reg.queue_position = None

        promoted_reg_id = None
        promoted_student_id = None

        if old_status == RegistrationStatus.CONFIRMED:
            # Uvolnilo se místo v kapacitě -> posun prvního v pořadníku (FIFO)
            first_waiting = db.query(Registration).filter(
                Registration.term_id == reg.term_id,
                Registration.status == RegistrationStatus.WAITING_LIST,
                Registration.queue_position == 1
            ).first()

            if first_waiting:
                first_waiting.status = RegistrationStatus.CONFIRMED
                first_waiting.queue_position = None
                promoted_reg_id = first_waiting.id
                promoted_student_id = first_waiting.student_id

                # Posun všech zbývajících v pořadníku o -1 pozici
                db.query(Registration).filter(
                    Registration.term_id == reg.term_id,
                    Registration.status == RegistrationStatus.WAITING_LIST,
                    Registration.queue_position > 1
                ).update(
                    {Registration.queue_position: Registration.queue_position - 1},
                    synchronize_session="fetch"
                )

        elif old_status == RegistrationStatus.WAITING_LIST and old_queue_pos is not None:
            # Zrušena přihláška v pořadníku -> posun všech za ním
            db.query(Registration).filter(
                Registration.term_id == reg.term_id,
                Registration.status == RegistrationStatus.WAITING_LIST,
                Registration.queue_position > old_queue_pos
            ).update(
                {Registration.queue_position: Registration.queue_position - 1},
                synchronize_session="fetch"
            )

        db.commit()

        message = "Přihláška byla zrušena a záznam archivován pro audit."
        if promoted_reg_id:
            message += f" Místo bylo uvolněno a první student z pořadníku (ID {promoted_student_id}) byl potvrzen."

        return RegistrationCancelResponse(
            cancelled_registration_id=reg.id,
            status=reg.status,
            message=message,
            promoted_student_id=promoted_student_id,
            promoted_registration_id=promoted_reg_id
        )

    @staticmethod
    def _build_response(reg: Registration) -> RegistrationResponse:
        return RegistrationResponse(
            id=reg.id,
            student_id=reg.student_id,
            term_id=reg.term_id,
            status=reg.status,
            queue_position=reg.queue_position,
            created_at=reg.created_at,
            cancelled_at=reg.cancelled_at,
            admin_override=reg.admin_override,
            admin_override_reason=reg.admin_override_reason,
            student_name=f"{reg.student.first_name} {reg.student.last_name}" if reg.student else None,
            course_name=reg.term.course.name if reg.term and reg.term.course else None
        )
