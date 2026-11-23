"""
End-to-end uživatelské testy (HTTP vrstva -> Business vrstva -> DB).
Simulují kompletní průchod aplikací přes FastAPI TestClient se stejnými JSON payloady,
jaké posílá webové rozhraní (app.js).
"""
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app.core.config import settings
from src.app.core.database import Base, get_db
from src.app.main import app
from src.app.models import Lecturer, Student


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Seed základního lektora a studenta pro testy přihlášení
    db = TestingSession()
    db.add(Lecturer(first_name="Petr", last_name="Novák", email="petr.novak@akademietrutnov.cz"))
    db.add(Student(first_name="Alena", last_name="Černá", email="alena.cerna@example.cz"))
    db.commit()
    db.close()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_full_user_journey_e2e(client: TestClient):
    today = date.today()

    # 1. Dostupnost frontendu a hlavička proti cachování
    r_home = client.get("/")
    assert r_home.status_code == 200
    assert "no-store" in r_home.headers.get("cache-control", "")
    assert "Akademie Trutnov" in r_home.text

    r_js = client.get("/static/app.js")
    assert r_js.status_code == 200
    assert "no-store" in r_js.headers.get("cache-control", "")

    # 2. Přihlášení všech 3 rolí + zamítnutí špatného hesla
    r_admin = client.post("/api/v1/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD,
    })
    assert r_admin.status_code == 200
    assert r_admin.json()["role"] == "admin"

    r_lec = client.post("/api/v1/auth/login", json={
        "email": "petr.novak@akademietrutnov.cz",
        "password": settings.LECTURER_DEMO_PASSWORD,
    })
    assert r_lec.status_code == 200
    assert r_lec.json()["role"] == "lecturer"
    lecturer_id = r_lec.json()["user_id"]

    r_stu = client.post("/api/v1/auth/login", json={
        "email": "alena.cerna@example.cz",
        "password": settings.STUDENT_DEMO_PASSWORD,
    })
    assert r_stu.status_code == 200
    assert r_stu.json()["role"] == "student"

    r_bad = client.post("/api/v1/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": "wrong-password",
    })
    assert r_bad.status_code == 401

    # 3. Admin založí kurz a termín s kapacitou 1 (pro otestování pořadníku)
    r_course = client.post("/api/v1/courses", json={
        "name": "Praktický SQL pro analytiky",
        "annotation": "Ukázkový testovací kurz",
        "hours_duration": 16,
        "price": 6900,
        "is_accredited": True,
    })
    assert r_course.status_code == 201
    course_id = r_course.json()["id"]

    d_from = (today + timedelta(days=10)).isoformat()
    d_to = (today + timedelta(days=12)).isoformat()
    r_term = client.post("/api/v1/terms", json={
        "course_id": course_id,
        "date_from": d_from,
        "date_to": d_to,
        "location": "Trutnov - Centrum",
        "classroom": "Učebna C1",
        "capacity": 1,
        "lecturers": [{"lecturer_id": lecturer_id, "taught_hours": 16}],
    })
    assert r_term.status_code == 201
    term_data = r_term.json()
    term_id = term_data["id"]
    assert term_data["confirmed_students_count"] == 0
    assert term_data["waiting_list_count"] == 0

    # Časová kolize lektora musí být zamítnuta
    r_conflict = client.post("/api/v1/terms", json={
        "course_id": course_id,
        "date_from": d_from,
        "date_to": d_to,
        "location": "Náchod",
        "classroom": "Učebna 2",
        "capacity": 5,
        "lecturers": [{"lecturer_id": lecturer_id, "taught_hours": 8}],
    })
    assert r_conflict.status_code == 400

    # 4. Samoobslužný zápis nového studenta -> CONFIRMED (kapacita 1/1 naplněna)
    r_self1 = client.post("/api/v1/registrations/self", json={
        "first_name": "Lukáš",
        "last_name": "Testovací",
        "email": "lukas.test@example.cz",
        "phone": "+420 608 111 222",
        "term_id": term_id,
    })
    assert r_self1.status_code == 201
    reg1 = r_self1.json()
    assert reg1["status"] == "CONFIRMED"
    assert reg1["student_email"] == "lukas.test@example.cz"

    # 5. Samoobslužný zápis existující studentky na plný termín -> WAITING_LIST #1
    r_self2 = client.post("/api/v1/registrations/self", json={
        "first_name": "Alena",
        "last_name": "Černá",
        "email": "alena.cerna@example.cz",
        "term_id": term_id,
    })
    assert r_self2.status_code == 201
    reg2 = r_self2.json()
    assert reg2["status"] == "WAITING_LIST"
    assert reg2["queue_position"] == 1

    # Kontrola historie studentky (Moje přihlášky)
    r_my = client.get(f"/api/v1/registrations/student/{reg2['student_id']}")
    assert r_my.status_code == 200
    assert len(r_my.json()) == 1
    assert r_my.json()[0]["status"] == "WAITING_LIST"

    # 6. Odhlášení Lukáše -> Auditní uchování + automatický posun Aleny na CONFIRMED
    r_cancel = client.post(f"/api/v1/registrations/{reg1['id']}/cancel")
    assert r_cancel.status_code == 200
    assert r_cancel.json()["promoted_registration_id"] == reg2["id"]

    r_term_regs = client.get(f"/api/v1/registrations/term/{term_id}")
    assert r_term_regs.status_code == 200
    by_id = {r["id"]: r for r in r_term_regs.json()}
    assert by_id[reg1["id"]]["status"] == "CANCELLED"
    assert by_id[reg2["id"]]["status"] == "CONFIRMED"

    # 7. Lektor zapíše docházku Aleně (přesný payload z app.js) a vystaví osvědčení
    r_att = client.post("/api/v1/attendance", json={
        "registration_id": reg2["id"],
        "records": [{"date": today.isoformat(), "is_present": True, "note": "Přítomna"}],
    })
    assert r_att.status_code == 201

    r_sum_before = client.get(f"/api/v1/attendance/summary/{reg2['id']}")
    assert r_sum_before.status_code == 200
    s_before = r_sum_before.json()
    assert s_before["attendance_percentage"] == 100.0
    assert s_before["meets_minimum_requirement"] is True
    assert s_before["certificate_number"] is None

    r_cert = client.post("/api/v1/certificates/issue", json={
        "registration_id": reg2["id"],
        "lecturer_approved": True,
    })
    assert r_cert.status_code == 201
    cert_num = r_cert.json()["certificate_number"]
    assert cert_num.startswith("TRU-")

    # Po vystavení musí summary vracet číslo osvědčení i schválení
    r_sum_after = client.get(f"/api/v1/attendance/summary/{reg2['id']}")
    assert r_sum_after.status_code == 200
    assert r_sum_after.json()["certificate_number"] == cert_num
    assert r_sum_after.json()["lecturer_approved"] is True

    # Načtení detailu osvědčení (pro tiskový modal)
    r_cert_get = client.get(f"/api/v1/certificates/{cert_num}")
    assert r_cert_get.status_code == 200
    assert r_cert_get.json()["student_name"] == "Alena Černá"

    # Neměnnost osvědčení (opětovné vystavení musí selhat)
    r_cert_dup = client.post("/api/v1/certificates/issue", json={
        "registration_id": reg2["id"],
        "lecturer_approved": True,
    })
    assert r_cert_dup.status_code == 400

    # 8. Manažerské reporty – ověření všech polí používaných v app.js (žádné undefined!)
    r_occ = client.get("/api/v1/reports/occupancy")
    assert r_occ.status_code == 200
    occ_item = r_occ.json()[0]
    for key in ("term_id", "course_name", "date_from", "date_to", "capacity", "confirmed_count", "waiting_count", "occupancy_percentage"):
        assert key in occ_item and occ_item[key] is not None

    r_lec_rep = client.get("/api/v1/reports/lecturer-hours")
    assert r_lec_rep.status_code == 200
    lec_item = r_lec_rep.json()[0]
    for key in ("lecturer_id", "lecturer_name", "terms_count", "total_hours_taught"):
        assert key in lec_item and lec_item[key] is not None

    r_multi = client.get("/api/v1/reports/multi-course-students?year=2026")
    assert r_multi.status_code == 200
