from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from src.app.models.term import Term
from src.app.models.registration import Registration
from src.app.models.lecturer import Lecturer
from src.app.models.term_lecturer import TermLecturer
from src.app.models.student import Student
from src.app.models.enums import RegistrationStatus
from src.app.schemas.report import TermOccupancyReport, LecturerHoursReport, MultiCourseStudentReport

class ReportService:
    @staticmethod
    def get_term_occupancy(db: Session) -> list[TermOccupancyReport]:
        terms = db.query(Term).all()
        reports = []
        for t in terms:
            conf_count = db.query(Registration).filter(
                Registration.term_id == t.id,
                Registration.status == RegistrationStatus.CONFIRMED
            ).count()

            wait_count = db.query(Registration).filter(
                Registration.term_id == t.id,
                Registration.status == RegistrationStatus.WAITING_LIST
            ).count()

            pct = (conf_count / t.capacity * 100.0) if t.capacity > 0 else 0.0

            reports.append(TermOccupancyReport(
                term_id=t.id,
                course_name=t.course.name if t.course else "Neznámý kurz",
                date_from=t.date_from,
                date_to=t.date_to,
                capacity=t.capacity,
                confirmed_count=conf_count,
                waiting_count=wait_count,
                occupancy_percentage=round(pct, 2)
            ))
        return reports

    @staticmethod
    def get_lecturer_hours(db: Session) -> list[LecturerHoursReport]:
        lecturers = db.query(Lecturer).all()
        reports = []
        for l in lecturers:
            total_hours = db.query(func.coalesce(func.sum(TermLecturer.taught_hours), 0)).filter(
                TermLecturer.lecturer_id == l.id
            ).scalar()

            terms_cnt = db.query(TermLecturer).filter(TermLecturer.lecturer_id == l.id).count()

            reports.append(LecturerHoursReport(
                lecturer_id=l.id,
                lecturer_name=f"{l.first_name} {l.last_name}",
                total_hours_taught=int(total_hours),
                terms_count=terms_cnt
            ))
        return reports

    @staticmethod
    def get_multi_course_students(db: Session, year: int) -> list[MultiCourseStudentReport]:
        # Najít studenty přihlášené na víc než 1 kurz v daném kalendářním roce
        active_regs = (
            db.query(Registration)
            .join(Term, Registration.term_id == Term.id)
            .filter(
                extract('year', Term.date_from) == year,
                Registration.status.in_([RegistrationStatus.CONFIRMED, RegistrationStatus.WAITING_LIST])
            )
            .all()
        )

        student_courses: dict[int, set[str]] = {}
        student_obj_map: dict[int, Student] = {}

        for r in active_regs:
            s_id = r.student_id
            c_name = r.term.course.name if r.term and r.term.course else f"Kurz {r.term.course_id}"
            if s_id not in student_courses:
                student_courses[s_id] = set()
                student_obj_map[s_id] = r.student
            student_courses[s_id].add(c_name)

        reports = []
        for s_id, courses in student_courses.items():
            if len(courses) > 1:
                student = student_obj_map[s_id]
                reports.append(MultiCourseStudentReport(
                    student_id=s_id,
                    student_name=f"{student.first_name} {student.last_name}" if student else "Neznámý",
                    email=student.email if student else "",
                    year=year,
                    courses_count=len(courses),
                    courses=list(courses)
                ))

        return reports
