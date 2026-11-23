import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from src.app.core.database import Base
from src.app.models import Course, Term, Lecturer, TermLecturer, Student, Registration, RegistrationStatus, Attendance, Certificate
from src.app.schemas.registration import RegistrationCreate, SelfRegistrationCreate
from src.app.schemas.certificate import CertificateIssueRequest
from src.app.schemas.attendance import AttendanceBulkCreate, AttendanceRecord
from src.app.schemas.term import TermCreate, TermLecturerAssign
from src.app.services.registration_service import RegistrationService
from src.app.services.certificate_service import CertificateService
from src.app.services.attendance_service import AttendanceService
from src.app.services.term_service import TermService

# In-memory databáze pro rychlé a izolované unit/integrační testy
@pytest.fixture
def db_session():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def sample_data(db_session):
    course = Course(
        name="Testovací kurz Python",
        annotation="Anotace",
        hours_duration=20,
        price=Decimal("5000.00"),
        is_accredited=True
    )
    db_session.add(course)
    db_session.flush()

    today = date.today()
    # Termín se striktní kapacitou 2 místa
    term = Term(
        course_id=course.id,
        date_from=today + timedelta(days=10),
        date_to=today + timedelta(days=12),
        location="Trutnov",
        classroom="Učebna 1",
        capacity=2
    )
    db_session.add(term)
    db_session.flush()

    # Vytvoření 3 studentů
    s1 = Student(first_name="Jan", last_name="Novák", email="jan@test.cz")
    s2 = Student(first_name="Petr", last_name="Svoboda", email="petr@test.cz")
    s3 = Student(first_name="Eva", last_name="Bílá", email="eva@test.cz")
    db_session.add_all([s1, s2, s3])
    db_session.commit()

    return {"course": course, "term": term, "students": [s1, s2, s3]}

def test_rule_capacity_and_fifo_queue(db_session, sample_data):
    """
    Ověření pravidla 1 & 2:
    - Kapacitu (2) nelze překročit.
    - 3. student je automaticky zařazen do pořadníku na pozici 1.
    """
    term = sample_data["term"]
    students = sample_data["students"]

    # 1. Zápis studenta 1 -> CONFIRMED
    reg1 = RegistrationService.register_student(
        db_session,
        RegistrationCreate(student_id=students[0].id, term_id=term.id)
    )
    assert reg1.status == RegistrationStatus.CONFIRMED
    assert reg1.queue_position is None

    # 2. Zápis studenta 2 -> CONFIRMED (kapacita 2/2 naplněna)
    reg2 = RegistrationService.register_student(
        db_session,
        RegistrationCreate(student_id=students[1].id, term_id=term.id)
    )
    assert reg2.status == RegistrationStatus.CONFIRMED
    assert reg2.queue_position is None

    # 3. Zápis studenta 3 -> WAITING_LIST, pozice 1 (FIFO)
    reg3 = RegistrationService.register_student(
        db_session,
        RegistrationCreate(student_id=students[2].id, term_id=term.id)
    )
    assert reg3.status == RegistrationStatus.WAITING_LIST
    assert reg3.queue_position == 1

    # Ověření, že počet potvrzených nepřekročil kapacitu 2
    confirmed_total = db_session.query(Registration).filter(
        Registration.term_id == term.id,
        Registration.status == RegistrationStatus.CONFIRMED
    ).count()
    assert confirmed_total == 2

def test_rule_cancellation_audit_and_auto_promote(db_session, sample_data):
    """
    Ověření pravidla 3 & 4:
    - Zrušená přihláška se fyzicky nemaže (audit).
    - První student z pořadníku je automaticky posunut na uvolněné místo.
    """
    term = sample_data["term"]
    students = sample_data["students"]

    reg1 = RegistrationService.register_student(db_session, RegistrationCreate(student_id=students[0].id, term_id=term.id))
    reg2 = RegistrationService.register_student(db_session, RegistrationCreate(student_id=students[1].id, term_id=term.id))
    reg3 = RegistrationService.register_student(db_session, RegistrationCreate(student_id=students[2].id, term_id=term.id))

    # Zrušení přihlášky studenta 1
    cancel_res = RegistrationService.cancel_registration(db_session, reg1.id)
    assert cancel_res.status == RegistrationStatus.CANCELLED
    assert cancel_res.promoted_student_id == students[2].id

    # Kontrola zrušené přihlášky v DB (zůstává pro audit!)
    db_reg1 = db_session.query(Registration).filter(Registration.id == reg1.id).first()
    assert db_reg1 is not None
    assert db_reg1.status == RegistrationStatus.CANCELLED
    assert db_reg1.cancelled_at is not None

    # Kontrola studenta 3 (původně náhradník) -> nyní CONFIRMED
    db_reg3 = db_session.query(Registration).filter(Registration.id == reg3.id).first()
    assert db_reg3.status == RegistrationStatus.CONFIRMED
    assert db_reg3.queue_position is None

def test_rule_no_concurrent_registration_same_course(db_session, sample_data):
    """
    Ověření pravidla o zákazu souběhu aktivních přihlášek na stejný kurz.
    """
    course = sample_data["course"]
    students = sample_data["students"]
    today = date.today()

    # Druhý termín téhož kurzu
    term2 = Term(
        course_id=course.id,
        date_from=today + timedelta(days=20),
        date_to=today + timedelta(days=22),
        location="Trutnov",
        classroom="Učebna 2",
        capacity=5
    )
    db_session.add(term2)
    db_session.commit()

    # Přihlášení studenta 1 na termín 1
    RegistrationService.register_student(db_session, RegistrationCreate(student_id=students[0].id, term_id=sample_data["term"].id))

    # Pokus o přihlášení studenta 1 na termín 2 stejného kurzu -> musí vyhodit výjimku 400
    with pytest.raises(HTTPException) as exc_info:
        RegistrationService.register_student(db_session, RegistrationCreate(student_id=students[0].id, term_id=term2.id))
    assert exc_info.value.status_code == 400

def test_rule_certificate_issuing_and_immutability(db_session, sample_data):
    """
    Ověření pravidel pro osvědčení:
    - Vyžaduje minimální docházku 70 % a souhlas lektora.
    - Číslo je unikátní.
    - Již vydané osvědčení nelze znovu vystavit/změnit (neměnnost).
    """
    term = sample_data["term"]
    student = sample_data["students"][0]

    reg = RegistrationService.register_student(db_session, RegistrationCreate(student_id=student.id, term_id=term.id))

    # Zápis docházky: 3 dny, přítomen 1 den (33 % < 70 %) -> nesplňuje!
    AttendanceService.log_attendance(db_session, AttendanceBulkCreate(
        registration_id=reg.id,
        records=[
            AttendanceRecord(date=term.date_from, is_present=True),
            AttendanceRecord(date=term.date_from + timedelta(days=1), is_present=False),
            AttendanceRecord(date=term.date_to, is_present=False),
        ]
    ))

    # Pokus o vystavení certifikátu při nedostatečné docházce -> chyba
    with pytest.raises(HTTPException) as exc_info:
        CertificateService.issue_certificate(db_session, CertificateIssueRequest(registration_id=reg.id, lecturer_approved=True))
    assert exc_info.value.status_code == 400
    assert "70%" in exc_info.value.detail

    # Doplnění docházky na 2/3 (66.7 % stále málo), pak 3/3 (100 %) -> splněno
    AttendanceService.log_attendance(db_session, AttendanceBulkCreate(
        registration_id=reg.id,
        records=[
            AttendanceRecord(date=term.date_from + timedelta(days=1), is_present=True),
            AttendanceRecord(date=term.date_to, is_present=True),
        ]
    ))

    # Úspěšné vystavení certifikátu
    cert = CertificateService.issue_certificate(db_session, CertificateIssueRequest(registration_id=reg.id, lecturer_approved=True))
    assert cert.certificate_number.startswith("TRU-")
    assert cert.registration_id == reg.id

    # Pokus o opětovné vystavení (porušení neměnnosti) -> chyba
    with pytest.raises(HTTPException) as exc_info2:
        CertificateService.issue_certificate(db_session, CertificateIssueRequest(registration_id=reg.id, lecturer_approved=True))
    assert exc_info2.value.status_code == 400
    assert "neměnné" in exc_info2.value.detail


def test_rule_late_registration_admin_override(db_session, sample_data):
    """
    Ověření pravidla 4 (ADR-003):
    - Zápis po zahájení termínu (date_from <= today) je standardně zakázán (HTTP 400).
    - Administrátor může povolit zápis s explicitním admin_override=True a důvodem.
    """
    course = sample_data["course"]
    student = sample_data["students"][0]
    today = date.today()

    # Termín, který již začal před 2 dny
    past_term = Term(
        course_id=course.id,
        date_from=today - timedelta(days=2),
        date_to=today + timedelta(days=2),
        location="Trutnov",
        classroom="Učebna 3",
        capacity=5
    )
    db_session.add(past_term)
    db_session.commit()

    # 1. Běžný pokus o zápis bez administrátorské výjimky -> musí selhat s kódem 400
    with pytest.raises(HTTPException) as exc_info:
        RegistrationService.register_student(
            db_session,
            RegistrationCreate(student_id=student.id, term_id=past_term.id, admin_override=False)
        )
    assert exc_info.value.status_code == 400
    assert "zahájen" in exc_info.value.detail

    # 2. Zápis administrátorem s výjimkou a povinným auditním důvodem -> úspěch
    reg = RegistrationService.register_student(
        db_session,
        RegistrationCreate(
            student_id=student.id,
            term_id=past_term.id,
            admin_override=True,
            admin_override_reason="Schváleno ředitelkou centra na základě telefonické žádosti"
        )
    )
    assert reg.status == RegistrationStatus.CONFIRMED
    assert reg.admin_override is True
    assert reg.admin_override_reason == "Schváleno ředitelkou centra na základě telefonické žádosti"

    # Ověření uložení v DB pro audit
    db_reg = db_session.query(Registration).filter(Registration.id == reg.id).first()
    assert db_reg.admin_override is True
    assert db_reg.admin_override_reason == "Schváleno ředitelkou centra na základě telefonické žádosti"


def test_rule_lecturer_schedule_conflict(db_session, sample_data):
    """
    Ověření pravidla o ochraně před časovou kolizí lektorů (ADR-005):
    - Lektor nemůže být přiřazen k termínu, který se časově překrývá s jiným termínem, kde již učí.
    """
    course = sample_data["course"]
    today = date.today()

    lecturer = Lecturer(
        first_name="Karel",
        last_name="Vomáčka",
        email="karel.vomacka@test.cz",
        phone="+420 777 000 111"
    )
    db_session.add(lecturer)
    db_session.commit()

    # 1. Vytvoření prvního termínu: dny 10 až 15
    term1 = TermService.create(
        db_session,
        TermCreate(
            course_id=course.id,
            date_from=today + timedelta(days=10),
            date_to=today + timedelta(days=15),
            location="Trutnov",
            classroom="Učebna 1",
            capacity=10,
            lecturers=[TermLecturerAssign(lecturer_id=lecturer.id, taught_hours=20)]
        )
    )
    assert term1.id is not None

    # 2. Pokus o vytvoření druhého termínu s kolidujícím termínem (dny 13 až 18) -> chyba 400
    with pytest.raises(HTTPException) as exc_info:
        TermService.create(
            db_session,
            TermCreate(
                course_id=course.id,
                date_from=today + timedelta(days=13),
                date_to=today + timedelta(days=18),
                location="Náchod",
                classroom="Učebna 2",
                capacity=8,
                lecturers=[TermLecturerAssign(lecturer_id=lecturer.id, taught_hours=15)]
            )
        )
    assert exc_info.value.status_code == 400
    assert "Časová kolize lektora" in exc_info.value.detail

    # 3. Vytvoření nekolidujícího termínu (dny 20 až 25) -> úspěch
    term2 = TermService.create(
        db_session,
        TermCreate(
            course_id=course.id,
            date_from=today + timedelta(days=20),
            date_to=today + timedelta(days=25),
            location="Náchod",
            classroom="Učebna 2",
            capacity=8,
            lecturers=[TermLecturerAssign(lecturer_id=lecturer.id, taught_hours=15)]
        )
    )
    assert term2.id is not None


def test_rule_student_self_registration_and_history(db_session, sample_data):
    """
    Ověření samoobslužného zápisu studenta (ADR-007):
    - Nový zájemce podle e-mailu automaticky založí záznam Student a vytvoří přihlášku.
    - Opakovaný samoobslužný zápis stejným e-mailem znovu použije existující profil a dodrží obchodní pravidla.
    - Přehled přihlášek studenta vrací jeho vlastní záznamy.
    """
    term = sample_data["term"]

    # 1. Samoobslužný zápis úplně nového zájemce
    reg1 = RegistrationService.self_register(
        db_session,
        SelfRegistrationCreate(
            first_name="Klára",
            last_name="Dvořáková",
            email="Klara.Dvorakova@Test.cz",
            phone="+420 602 111 222",
            term_id=term.id,
        ),
    )
    assert reg1.status == RegistrationStatus.CONFIRMED
    assert reg1.student_email == "klara.dvorakova@test.cz"

    # 2. Pokus o druhý zápis téhož e-mailu na stejný kurz -> musí zachytit pravidlo zákazu souběhu
    with pytest.raises(HTTPException) as exc_info:
        RegistrationService.self_register(
            db_session,
            SelfRegistrationCreate(
                first_name="Klára",
                last_name="Dvořáková",
                email="klara.dvorakova@test.cz",
                term_id=term.id,
            ),
        )
    assert exc_info.value.status_code == 400

    # Student nesmí být založen duplicitně
    matching_students = db_session.query(Student).filter(Student.email == "klara.dvorakova@test.cz").all()
    assert len(matching_students) == 1

    # 3. Načtení historie přihlášek konkrétního studenta
    history = RegistrationService.get_by_student(db_session, reg1.student_id)
    assert len(history) == 1
    assert history[0].id == reg1.id
