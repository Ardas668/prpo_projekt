from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.app.models.term import Term
from src.app.models.course import Course
from src.app.models.lecturer import Lecturer
from src.app.models.term_lecturer import TermLecturer
from src.app.models.registration import Registration
from src.app.models.enums import RegistrationStatus
from src.app.schemas.term import TermCreate, TermResponse, TermLecturerResponse

class TermService:
    @staticmethod
    def get_all(db: Session) -> list[TermResponse]:
        terms = db.query(Term).all()
        result = []
        for t in terms:
            result.append(TermService._build_term_response(db, t))
        return result

    @staticmethod
    def get_by_id(db: Session, term_id: int) -> Term | None:
        return db.query(Term).filter(Term.id == term_id).first()

    @staticmethod
    def get_term_response(db: Session, term_id: int) -> TermResponse:
        term = TermService.get_by_id(db, term_id)
        if not term:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Termín nenalezen.")
        return TermService._build_term_response(db, term)

    @staticmethod
    def create(db: Session, term_in: TermCreate) -> TermResponse:
        course = db.query(Course).filter(Course.id == term_in.course_id).first()
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Přiřazovaný kurz neexistuje.")

        if term_in.date_from > term_in.date_to:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Datum začátku nemůže být po datu konce.")

        term = Term(
            course_id=term_in.course_id,
            date_from=term_in.date_from,
            date_to=term_in.date_to,
            location=term_in.location,
            classroom=term_in.classroom,
            capacity=term_in.capacity
        )
        db.add(term)
        db.flush()

        for l_assign in term_in.lecturers:
            lecturer = db.query(Lecturer).filter(Lecturer.id == l_assign.lecturer_id).first()
            if not lecturer:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lektor s ID {l_assign.lecturer_id} neexistuje.")

            # Kontrola časové kolize lektora s jinými termíny
            conflict_term = (
                db.query(Term)
                .join(TermLecturer, Term.id == TermLecturer.term_id)
                .filter(
                    TermLecturer.lecturer_id == l_assign.lecturer_id,
                    Term.id != term.id,
                    Term.date_from <= term_in.date_to,
                    Term.date_to >= term_in.date_from
                )
                .first()
            )
            if conflict_term:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Časová kolize lektora: {lecturer.first_name} {lecturer.last_name} již učí termín ID {conflict_term.id} v období od {conflict_term.date_from} do {conflict_term.date_to}."
                )

            db.add(TermLecturer(
                term_id=term.id,
                lecturer_id=l_assign.lecturer_id,
                taught_hours=l_assign.taught_hours
            ))

        db.commit()
        db.refresh(term)
        return TermService._build_term_response(db, term)

    @staticmethod
    def _build_term_response(db: Session, term: Term) -> TermResponse:
        confirmed = db.query(Registration).filter(
            Registration.term_id == term.id,
            Registration.status == RegistrationStatus.CONFIRMED
        ).count()

        waiting = db.query(Registration).filter(
            Registration.term_id == term.id,
            Registration.status == RegistrationStatus.WAITING_LIST
        ).count()

        lecturers_resp = []
        for tl in term.term_lecturers:
            l = tl.lecturer
            lecturers_resp.append(TermLecturerResponse(
                lecturer_id=tl.lecturer_id,
                taught_hours=tl.taught_hours,
                lecturer_name=f"{l.first_name} {l.last_name}" if l else None
            ))

        return TermResponse(
            id=term.id,
            course_id=term.course_id,
            date_from=term.date_from,
            date_to=term.date_to,
            location=term.location,
            classroom=term.classroom,
            capacity=term.capacity,
            confirmed_students_count=confirmed,
            waiting_list_count=waiting,
            is_full=(confirmed >= term.capacity),
            lecturers=lecturers_resp
        )
