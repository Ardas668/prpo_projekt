from sqlalchemy.orm import Session
from src.app.models.course import Course
from src.app.schemas.course import CourseCreate

class CourseService:
    @staticmethod
    def get_all(db: Session) -> list[Course]:
        return db.query(Course).all()

    @staticmethod
    def get_by_id(db: Session, course_id: int) -> Course | None:
        return db.query(Course).filter(Course.id == course_id).first()

    @staticmethod
    def create(db: Session, course_in: CourseCreate) -> Course:
        course = Course(**course_in.model_dump())
        db.add(course)
        db.commit()
        db.refresh(course)
        return course
