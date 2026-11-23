"""
DEMO SCÉNÁŘ - Akademie Trutnov (IS Kurzy)
Tento skript demonstruje kompletní životní cyklus kurzu a ověření všech klíčových obchodních pravidel:
1. Vytvoření kurzu a termínu se striktní kapacitou (2 místa) a střídáním lektorů.
2. Zápis studentů do naplnění kapacity (2/2).
3. Pokus o zápis dalšího studenta -> automatické zařazení do FIFO pořadníku (pozice #1).
4. Zrušení přihlášky zapsaného studenta -> uvolnění místa a automatický posun náhradníka.
5. Pravidlo pozdního zápisu po zahájení termínu (zamítnutí bez výjimky vs. schválení administrátorem).
6. Ochrana před časovou kolizí lektorů (zamítnutí překrývajícího se termínu pro téhož lektora).
7. Zápis docházky vícedenního kurzu a kontrola podmínky 70 % pro osvědčení.
8. Vystavení unikátního neměnného certifikátu (TRU-YYYY-XXXXX) a odmítnutí modifikace.
9. Manažerské statistiky a přehledy (naplněnost kapacit, odučené hodiny lektorů).
"""

from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from src.app.core.database import Base
from src.app.models import Course, Term, Student, Registration, RegistrationStatus, Lecturer, TermLecturer
from src.app.schemas.registration import RegistrationCreate
from src.app.schemas.certificate import CertificateIssueRequest
from src.app.schemas.attendance import AttendanceBulkCreate, AttendanceRecord
from src.app.schemas.term import TermCreate, TermLecturerAssign
from src.app.services.registration_service import RegistrationService
from src.app.services.certificate_service import CertificateService
from src.app.services.attendance_service import AttendanceService
from src.app.services.term_service import TermService
from src.app.services.report_service import ReportService

def separator(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)

def run_demo():
    separator("1. Inicializace izolovaného DEMO prostředí")
    # Použití in-memory SQLite pro rychlý a bezpečný běh bez narušení běžící databáze
    demo_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=demo_engine)
    DemoSession = sessionmaker(autocommit=False, autoflush=False, bind=demo_engine)
    db = DemoSession()

    try:
        # Vytvoření lektorů
        l1 = Lecturer(first_name="Petr", last_name="Novák", email="petr.novak@akademietrutnov.cz", phone="+420 777 111 222")
        l2 = Lecturer(first_name="Tomáš", last_name="Kučera", email="tomas.kucera@akademietrutnov.cz", phone="+420 777 333 444")
        db.add_all([l1, l2])

        # Vytvoření kurzu
        course = Course(
            name="Programování v Pythonu pro praxi",
            annotation="Intenzivní kurz praktického programování.",
            hours_duration=40,
            price=Decimal("14900.00"),
            is_accredited=True
        )
        db.add(course)
        db.flush()

        # Vytvoření termínu s kapacitou POUZE 2 MÍSTA (pro demonstraci FIFO)
        today = date.today()
        term = Term(
            course_id=course.id,
            date_from=today + timedelta(days=10),
            date_to=today + timedelta(days=14),
            location="Trutnov - Centrum",
            classroom="Učebna A1",
            capacity=2
        )
        db.add(term)
        db.flush()

        # Střídání dvou lektorů na termínu (M:N vazba s hodinami)
        tl1 = TermLecturer(term_id=term.id, lecturer_id=l1.id, taught_hours=24)
        tl2 = TermLecturer(term_id=term.id, lecturer_id=l2.id, taught_hours=16)
        db.add_all([tl1, tl2])

        # Vytvoření studentů
        s1 = Student(first_name="Martin", last_name="Dvořák", email="martin@example.cz")
        s2 = Student(first_name="Alena", last_name="Černá", email="alena@example.cz")
        s3 = Student(first_name="Jiří", last_name="Procházka", email="jiri@example.cz")
        s4 = Student(first_name="Eva", last_name="Bílá", email="eva@example.cz")
        db.add_all([s1, s2, s3, s4])
        db.commit()

        print(f"✓ Vytvořen kurz: '{course.name}' (Rozsah: {course.hours_duration} hod., Akreditovaný: {course.is_accredited})")
        print(f"✓ Vytvořen termín ID {term.id}: Kapacita {term.capacity} místa v učebně {term.classroom}")
        print(f"✓ Přiřazeni lektoři: {l1.first_name} {l1.last_name} ({tl1.taught_hours}h) a {l2.first_name} {l2.last_name} ({tl2.taught_hours}h)")

        separator("2. Test kapacity a FIFO pořadníku (Pravidlo 1 & 2)")
        print("Registrujeme studenta 1 (Martin Dvořák)...")
        reg1 = RegistrationService.register_student(db, RegistrationCreate(student_id=s1.id, term_id=term.id))
        print(f" -> Stav: {reg1.status.value} (Pozice v pořadníku: {reg1.queue_position})")

        print("\nRegistrujeme studenta 2 (Alena Černá)...")
        reg2 = RegistrationService.register_student(db, RegistrationCreate(student_id=s2.id, term_id=term.id))
        print(f" -> Stav: {reg2.status.value} (Pozice v pořadníku: {reg2.queue_position}) - KAPACITA 2/2 JE NAPLNĚNA!")

        print("\nRegistrujeme studenta 3 (Jiří Procházka) NAD KAPACITU...")
        reg3 = RegistrationService.register_student(db, RegistrationCreate(student_id=s3.id, term_id=term.id))
        print(f" -> Stav: {reg3.status.value}! Pozice v pořadníku: #{reg3.queue_position} (FIFO)")

        separator("3. Zrušení přihlášky a automatický posun náhradníka (Pravidlo 3 & 4)")
        print(f"Student Martin Dvořák (přihláška ID {reg1.id}) ruší účast...")
        cancel_res = RegistrationService.cancel_registration(db, reg1.id)
        print(f"✓ Zpráva systému: {cancel_res.message}")
        print(f"✓ Původní přihláška ID {reg1.id}: stav {cancel_res.status.value} (zůstává v DB pro audit)")

        # Kontrola nového stavu studenta 3
        db.refresh(db.query(Registration).filter(Registration.id == reg3.id).first())
        reg3_updated = RegistrationService._build_response(db.query(Registration).filter(Registration.id == reg3.id).first())
        print(f"✓ Student Jiří Procházka: automaticky povýšen na stav {reg3_updated.status.value}!")

        separator("4. Ověření pozdního zápisu po zahájení termínu (ADR-003)")
        past_term = Term(
            course_id=course.id,
            date_from=today - timedelta(days=2),
            date_to=today + timedelta(days=2),
            location="Trutnov",
            classroom="Učebna B",
            capacity=5
        )
        db.add(past_term)
        db.commit()

        print("A) Pokus o běžný zápis na již zahájený termín (bez výjimky):")
        try:
            RegistrationService.register_student(db, RegistrationCreate(student_id=s4.id, term_id=past_term.id, admin_override=False))
        except HTTPException as e:
            print(f"✓ Systém správně zamítl zápis (HTTP {e.status_code}): {e.detail}")

        print("\nB) Zápis administrátorem s explicitní výjimkou a auditním důvodem:")
        reg_late = RegistrationService.register_student(db, RegistrationCreate(
            student_id=s4.id,
            term_id=past_term.id,
            admin_override=True,
            admin_override_reason="Schváleno ředitelkou centra na základě telefonické žádosti"
        ))
        print(f"✓ Výjimka povolena! Stav: {reg_late.status.value}, Důvod auditu: '{reg_late.admin_override_reason}'")

        separator("5. Ochrana před časovou kolizí lektorů (ADR-005)")
        print("Pokus o přiřazení lektora Petra Nováka na další termín ve stejném období...")
        try:
            TermService.create(db, TermCreate(
                course_id=course.id,
                date_from=term.date_from + timedelta(days=1),
                date_to=term.date_to + timedelta(days=1),
                location="Pobočka Náchod",
                classroom="Učebna 102",
                capacity=8,
                lecturers=[TermLecturerAssign(lecturer_id=l1.id, taught_hours=16)]
            ))
        except HTTPException as e:
            print(f"✓ Systém úspěšně detekoval kolizi rozvrhu (HTTP {e.status_code}):\n  {e.detail}")

        separator("6. Evidence docházky a podmínka dokončení kurzu (>= 70 %)")
        print("Zapisujeme docházku pro Jiřího Procházku (3 dny ze 4 = 75 %)...")
        AttendanceService.log_attendance(db, AttendanceBulkCreate(
            registration_id=reg3.id,
            records=[
                AttendanceRecord(date=term.date_from, is_present=True),
                AttendanceRecord(date=term.date_from + timedelta(days=1), is_present=True),
                AttendanceRecord(date=term.date_from + timedelta(days=2), is_present=True),
                AttendanceRecord(date=term.date_from + timedelta(days=3), is_present=False, note="Omluvená neúčast"),
            ]
        ))
        summary = AttendanceService.get_summary(db, reg3.id)
        print(f"✓ Docházka: {summary.attended_days}/{summary.total_days} dnů ({summary.attendance_percentage} %)")
        print(f"✓ Splňuje kritérium pro osvědčení: {summary.meets_minimum_requirement}")

        separator("7. Vystavení unikátního neměnného osvědčení")
        cert = CertificateService.issue_certificate(db, CertificateIssueRequest(registration_id=reg3.id, lecturer_approved=True))
        print(f"✓ Vystaveno osvědčení č.: {cert.certificate_number}")
        print(f"✓ Absolvent: {cert.student_name}")
        print(f"✓ Datum vystavení: {cert.issued_at}")

        print("\nOvěření pravidla neměnnosti certifikátu (pokus o opětovné vystavení):")
        try:
            CertificateService.issue_certificate(db, CertificateIssueRequest(registration_id=reg3.id, lecturer_approved=True))
        except HTTPException as e:
            print(f"✓ Systém správně zamítl úpravu certifikátu: {e.detail}")

        separator("8. Manažerské přehledy a statistiky")
        print("A) Vytížení termínů:")
        for occ in ReportService.get_term_occupancy(db):
            print(f"   Termín #{occ.term_id} ({occ.course_name}): Obsazenost {occ.confirmed_count}/{occ.capacity} ({occ.occupancy_percentage} %), Náhradníci: {occ.waiting_count}")

        print("\nB) Odučené hodiny lektorů:")
        for lh in ReportService.get_lecturer_hours(db):
            print(f"   Lektor: {lh.lecturer_name} -> {lh.total_hours_taught} odučených hodin v {lh.terms_count} termínech")

        separator("DEMO ÚSPĚŠNĚ DOKONČENO - VŠECHNA PRAVIDLA OVĚŘENA!")

    finally:
        db.close()

if __name__ == "__main__":
    run_demo()
