from datetime import date, timedelta
from decimal import Decimal
from src.app.core.database import SessionLocal, engine, Base
from src.app.models import (
    Course, Term, Lecturer, TermLecturer, Student, Registration, RegistrationStatus
)

def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Kontrola, zda již data neexistují
        if db.query(Course).count() > 0:
            print("Databáze již obsahuje data, seed přeskočen.")
            return

        print("Generuji syntetická ukázková data...")

        # 1. Kurzy
        c1 = Course(
            name="Programování v Pythonu pro praxi",
            annotation="Praktický rekvalifikační kurz moderního programování v Pythonu včetně práce s databázemi a API.",
            hours_duration=40,
            price=Decimal("14900.00"),
            is_accredited=True
        )
        c2 = Course(
            name="Tvorba webových aplikací v Reactu",
            annotation="Intenzivní firemní kurz zaměřený na stavbu moderních webových komponent.",
            hours_duration=32,
            price=Decimal("11500.00"),
            is_accredited=False
        )
        c3 = Course(
            name="Základy digitálního marketingu a SEO",
            annotation="Kurz zaměřený na online propagaci, sociální sítě a optimalizaci pro vyhledávače.",
            hours_duration=24,
            price=Decimal("8900.00"),
            is_accredited=True
        )
        c4 = Course(
            name="Účetnictví a daňová evidence",
            annotation="Kompletní příprava na vedení podvojného účetnictví pro malé a střední podniky.",
            hours_duration=50,
            price=Decimal("18500.00"),
            is_accredited=True
        )
        db.add_all([c1, c2, c3, c4])
        db.flush()

        # 2. Lektoři
        l1 = Lecturer(
            first_name="Petr",
            last_name="Novák",
            email="petr.novak@akademietrutnov.cz",
            phone="+420 777 123 456"
        )
        l2 = Lecturer(
            first_name="Jana",
            last_name="Svobodová",
            email="jana.svobodova@akademietrutnov.cz",
            phone="+420 777 654 321"
        )
        l3 = Lecturer(
            first_name="Tomáš",
            last_name="Kučera",
            email="tomas.kucera@akademietrutnov.cz",
            phone="+420 777 987 654"
        )
        db.add_all([l1, l2, l3])
        db.flush()

        # 3. Studenti (syntetická data)
        s1 = Student(first_name="Martin", last_name="Dvořák", email="martin.dvorak@example.cz", phone="+420 601 111 222")
        s2 = Student(first_name="Alena", last_name="Černá", email="alena.cerna@example.cz", phone="+420 602 222 333")
        s3 = Student(first_name="Jiří", last_name="Procházka", email="jiri.prochazka@example.cz", phone="+420 603 333 444")
        s4 = Student(first_name="Kateřina", last_name="Veselá", email="katerina.vesela@example.cz", phone="+420 604 444 555")
        s5 = Student(first_name="Michal", last_name="Horák", email="michal.horak@example.cz", phone="+420 605 555 666")
        db.add_all([s1, s2, s3, s4, s5])
        db.flush()

        # 4. Termíny
        today = date.today()
        # Termín 1: Python - schválně malá kapacita 2 místa pro snadnou demonstraci pořadníku!
        t1 = Term(
            course_id=c1.id,
            date_from=today + timedelta(days=14),
            date_to=today + timedelta(days=18),
            location="Trutnov - Centrum",
            classroom="Učebna A1 (PC laboratoř)",
            capacity=2
        )
        # Termín 2: React
        t2 = Term(
            course_id=c2.id,
            date_from=today + timedelta(days=21),
            date_to=today + timedelta(days=25),
            location="Trutnov - Centrum",
            classroom="Učebna B2",
            capacity=10
        )
        # Termín 3: Účetnictví
        t3 = Term(
            course_id=c4.id,
            date_from=today + timedelta(days=30),
            date_to=today + timedelta(days=40),
            location="Pobočka Náchod",
            classroom="Učebna 104",
            capacity=6
        )
        db.add_all([t1, t2, t3])
        db.flush()

        # 5. Přiřazení lektorů k termínům (M:N) - střídání 2 lektorů na termínu 1
        tl1 = TermLecturer(term_id=t1.id, lecturer_id=l1.id, taught_hours=24)
        tl2 = TermLecturer(term_id=t1.id, lecturer_id=l3.id, taught_hours=16)
        tl3 = TermLecturer(term_id=t2.id, lecturer_id=l2.id, taught_hours=32)
        tl4 = TermLecturer(term_id=t3.id, lecturer_id=l2.id, taught_hours=50)
        db.add_all([tl1, tl2, tl3, tl4])

        db.commit()
        print("Syntetická data úspěšně vytvořena!")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
