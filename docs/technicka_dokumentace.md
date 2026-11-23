# Technická dokumentace – Akademie Trutnov (IS pro správu kurzů)

**Předmět:** Pokročilé programování (PPRO), FIM UHK, ZS 2026/2027  
**Zadání:** Varianta C – Kurzy vzdělávacího centra (*Ing. Lucie Bartošová, Akademie Trutnov*)  
**Verze dokumentu:** 1.0  
**Datum:** 23. 11. 2026

---

## 1. Úvod a rozsah řešení

Informační systém **Akademie Trutnov** nahrazuje dosavadní ruční evidenci přihlášek v tabulkovém procesoru, papírové pořadníky a ruční vystavování osvědčení ve Wordu. Systém řeší celý životní cyklus vzdělávacího kurzu:

1. **Katalog kurzů** – evidence rekvalifikačních a firemních kurzů (název, anotace, rozsah v hodinách, cena, akreditace).
2. **Termíny kurzů a externí lektoři** – vypisování běhů v různých lokalitách a učebnách s proměnnou kapacitou, střídání více lektorů na jednom termínu s rozpadem odučených hodin a hlídáním časových kolizí.
3. **Přihlášky, kapacita a FIFO pořadník** – samoobslužné přihlašování zájemců i správa administrátorem, striktní nepřekročitelnost kapacity, nepřeskakovatelný pořadník náhradníků, automatický posun při uvolnění místa a auditní uchování zrušených přihlášek.
4. **Docházka a neměnná osvědčení** – evidence účasti po jednotlivých dnech, kontrola minimální docházky (≥ 70 %) a schválení lektorem, generování unikátního a zpětně neměnného evidenčního čísla (`TRU-YYYY-XXXX`).
5. **Manažerské přehledy a role** – reporty obsazenosti termínů, odučených hodin lektorů, vícekurzových studentů (včetně CSV exportu pro Excel) a oddělení uživatelských rolí (*Návštěvník*, *Student*, *Lektor*, *Administrátor*).

---

## 2. Architektura systému

Aplikace dodržuje **třívrstvou architekturu s jednosměrnými závislostmi** (*Prezentační vrstva → Byznys / Aplikační vrstva → Datová vrstva*). Každá vrstva má jasně vymezenou odpovědnost a nesmí obcházet vrstvu pod sebou:

| Vrstva | Umístění v kódu | Odpovědnost | Závislosti |
|---|---|---|---|
| **1. Prezentační vrstva** | `src/app/api/v1/endpoints/`, `src/app/schemas/`, `src/app/static/` | HTTP/REST endpointy FastAPI, typová validace Pydantic v2, webový SPA dashboard, OpenAPI/Swagger (`/docs`) | Pouze na byznys vrstvu (`services`) |
| **2. Byznys / aplikační vrstva** | `src/app/services/` | Vynucování obchodních pravidel (kapacity, FIFO pořadník, audit, kolize lektorů, limit docházky, neměnnost osvědčení, reporty) | Pouze na datovou vrstvu (`models`) |
| **3. Datová vrstva** | `src/app/models/`, `src/app/core/database.py`, `alembic/` | SQLAlchemy 2.0 ORM modely (8 entit), relační vazby a integritní omezení, verzované migrace Alembic, PostgreSQL 16 | Žádné zpětné závislosti na vyšší vrstvy |

### Technologický stack (ADR-002, ADR-004)
| Oblast | Technologie | Důvod volby |
|---|---|---|
| Backend & REST API | **Python 3.12 + FastAPI** | Automatická OpenAPI/Swagger dokumentace, silná typová validace přes Pydantic v2, přehledné routování. |
| ORM & Migrace | **SQLAlchemy 2.0 + Alembic** | Deklarativní relační modely, plná kontrola nad transakcemi a verzované migrace databázového schématu. |
| Databáze | **PostgreSQL 16 (Alpine)** | Plnohodnotný relační DBMS v Docker kontejneru s `healthcheckem` a perzistentním volume. |
| Frontend | **HTML5 + CSS3 + ES6 JS** | Jednoduchý SPA dashboard servírovaný přímo z FastAPI (bez nutnosti dalšího Node.js kontejneru). |
| Testování | **pytest + FastAPI TestClient** | Izolované běhy v in-memory SQLite v řádu zlomků sekundy; ověřuje doménové služby i HTTP vrstvu. |
| Kontejnerizace | **Docker + Docker Compose** | Spuštění celé aplikace (DB + migrace + seed + backend) jediným příkazem `docker compose up`. |

### Adresářová struktura projektu
```text
prpo_projekt/
├── alembic/                    # Konfigurace a verzované databázové migrace
│   └── versions/               # 304d31488d52_initial_schema.py
├── docs/
│   └── technicka_dokumentace.md
├── src/app/
│   ├── api/v1/endpoints/       # REST endpointy (auth, courses, terms, lecturers, students, registrations, attendance, certificates, reports)
│   ├── core/                   # config.py (Pydantic BaseSettings/.env), database.py
│   ├── models/                 # SQLAlchemy ORM entity a enumy
│   ├── schemas/                # Pydantic DTO schémata
│   ├── services/               # Doménová logika a vynucování obchodních pravidel
│   ├── static/                 # Webové rozhraní (index.html, app.js, style.css)
│   ├── main.py                 # Inicializace FastAPI, middleware proti cachování, routery
│   └── seed.py                 # Idempotentní inicializace syntetických dat
├── tests/
│   ├── test_business_rules.py  # Testy obchodních pravidel a autentizace (8 testů)
│   └── test_e2e_user_flows.py  # Kompletní HTTP end-to-end uživatelský scénář
├── demo.py                     # Konzolová demonstrace 8 kroků životního cyklu (izolovaná in-memory DB)
├── docker-compose.yml
├── Dockerfile
└── .env.example                # Šablona proměnných prostředí (skutečné .env je v .gitignore)
```

---

## 3. Datový model a databázové schéma

Doménový model tvoří **8 relačních entit**, z toho **2 plnohodnotné vazební tabulky M:N s vlastními atributy** (`term_lecturers` a `registrations`). Schéma je spravováno výhradně migracemi Alembic (`alembic upgrade head`).

| Tabulka | Primární klíč / Cizí klíče | Klíčové sloupce | Vazby |
|---|---|---|---|
| `courses` | `id` (PK) | `name`, `annotation`, `hours_duration`, `price`, `is_accredited` | 1:N → `terms` |
| `terms` | `id` (PK), `course_id` (FK → `courses.id`) | `date_from`, `date_to`, `location`, `classroom`, `capacity` | N:1 → `courses`, M:N → `lecturers`, M:N → `students` |
| `lecturers` | `id` (PK) | `first_name`, `last_name`, `email` (UNIQUE), `phone` | M:N → `terms` (přes `term_lecturers`) |
| `term_lecturers` | `(term_id, lecturer_id)` (složený PK, FK) | `taught_hours` | Vazební tabulka M:N pro střídání lektorů a rozpad hodin |
| `students` | `id` (PK) | `first_name`, `last_name`, `email` (UNIQUE), `phone` | M:N → `terms` (přes `registrations`) |
| `registrations` | `id` (PK), `student_id` (FK), `term_id` (FK) | `status` (ENUM), `queue_position`, `created_at`, `cancelled_at`, `admin_override`, `admin_override_reason` | Vazební tabulka M:N; 1:N → `attendances`, 1:0..1 → `certificates` |
| `attendances` | `id` (PK), `registration_id` (FK) | `date`, `is_present`, `note` | N:1 → `registrations` |
| `certificates` | `id` (PK), `registration_id` (FK, UNIQUE) | `certificate_number` (UNIQUE), `issued_at` | 1:1 → `registrations` (`ON DELETE RESTRICT`) |

### Klíčová integritní omezení na úrovni databáze
* **`students.email` a `lecturers.email` (`UNIQUE`)** – jednoznačná identifikace osob bez duplicitních záznamů.
* **`term_lecturers (term_id, lecturer_id)` (složený `PK`)** – zabraňuje dvojitému přiřazení téhož lektora ke stejnému termínu a uchovává jeho konkrétní rozpad odučených hodin (`taught_hours`).
* **`certificates.certificate_number` (`UNIQUE`)** – databázová pojistka proti opakování evidenčního čísla osvědčení.
* **`certificates.registration_id` (`UNIQUE`, `ON DELETE RESTRICT`)** – každé přihlášce náleží nejvýše jedno osvědčení a přihlášku s již vydaným osvědčením nelze smazat.
* **`registrations.status` (`ENUM`)** – povoluje pouze stavy `CONFIRMED`, `WAITING_LIST`, `CANCELLED` (fyzické mazání se neprovádí).

---

## 4. Klíčová místa návrhu a rozvedení otevřených bodů klienta

Zadání upozorňuje, že u Varianty C se návrh láme ve dvou zásadních oblastech: **pořadník náhradníků** a **pravidlo dokončení kurzu**. Níže je rozvedeno řešení všech 5 otevřených bodů ze zadání (navazující na stručné záznamy ADR-003 až ADR-008 v `README.md`).

### 4.1 Kapacita, FIFO pořadník, automatický posun a audit (Otevřený bod č. 2)
* **Problém:** Kapacitu nelze překročit, pořadí náhradníků se nesmí přeskakovat a při odhlášení účastníka musí být jasné, kdo postupuje. Zároveň se zrušená přihláška nesmí ztratit kvůli reklamacím.
* **Zvolené řešení:**
  1. Při vytváření přihlášky (`RegistrationService.register_student`) se spočítá počet přihlášek termínu ve stavu `CONFIRMED`. Je-li menší než `term.capacity`, přihláška vznikne jako `CONFIRMED` (`queue_position = NULL`). V opačném případě vznikne jako `WAITING_LIST` s `queue_position = MAX(queue_position) + 1`.
  2. Při zrušení přihlášky (`RegistrationService.cancel_registration`) se záznam **fyzicky nemaže** – nastaví se `status = CANCELLED`, vyplní se časové razítko `cancelled_at` a `queue_position = NULL`.
  3. Pokud šlo o potvrzenou přihlášku (`CONFIRMED`), systém v téže databázové transakci vyhledá prvního náhradníka (`queue_position == 1`), povýší jej na `CONFIRMED` (`queue_position = NULL`) a všem zbývajícím náhradníkům sníží `queue_position` o 1.
  4. Pokud se odhlásí samotný náhradník z pořadníku, posunou se o 1 pozici dopředu všichni náhradníci za ním.
* **Odolnost vůči změně názoru klienta:** Pokud by klient v budoucnu požadoval ruční potvrzování náhradníka (místo automatického posunu), stačí doplnit mezistav `OFFERED` do `RegistrationStatus` a oddělit krok nabídky od potvrzení bez zásahu do ostatních tabulek.

**Průběh transakce při zrušení potvrzené přihlášky (`POST /api/v1/registrations/{id}/cancel`):**
1. Přihlášce se změní stav na `CANCELLED`, zapíše se `cancelled_at = NOW()` a `queue_position = NULL` (záznam zůstává v databázi pro audit).
2. V téže transakci systém vyhledá náhradníka daného termínu s `status = WAITING_LIST` a `queue_position = 1`.
3. Pokud existuje, povýší jej na `CONFIRMED` (`queue_position = NULL`) a všem zbývajícím náhradníkům v pořadníku dekrementuje `queue_position` o 1.
4. Transakce se potvrdí (`COMMIT`) a API vrátí ID zrušené i povýšené přihlášky.

### 4.2 Pravidlo dokončení kurzu a neměnnost osvědčení (Otevřený bod č. 1)
* **Problém:** Klient uvádí jednou limit 70 % docházky, podruhé posouzení lektorem. Osvědčení se dříve vystavovala ručně a docházelo k duplicitám čísel.
* **Zvolené řešení:**
  1. **Konjunkce docházky a schválení:** `AttendanceService.get_summary()` vypočítá procento účasti z denních záznamů v tabulce `attendances` a ověří `attendance_percentage >= 70.0`. Současně `CertificateService.issue_certificate()` vyžaduje explicitní příznak `lecturer_approved = True` (potvrzený lektorem nebo administrátorem).
  2. **Generování unikátního čísla:** Při splnění obou podmínek systém vygeneruje evidenční číslo formátu `TRU-<ROK>-<0001..>`.
  3. **Neměnnost:** Pokud pro danou přihlášku již osvědčení existuje, pokus o opětovné vydání nebo přepis končí chybou `HTTP 400`. K osvědčení neexistuje žádný `PUT`/`PATCH`/`DELETE` endpoint.

### 4.3 Souběh termínů téhož kurzu (Otevřený bod č. 3)
* **Rozhodnutí (ADR-003):** Student nesmí mít současně více než jednu aktivní přihlášku (`CONFIRMED` nebo `WAITING_LIST`) na různé termíny téhož kurzu. Zabraňuje se tím spekulativnímu blokování kapacit. Po zrušení (`CANCELLED`) původní přihlášky se student může bez problému přihlásit na jiný termín.

### 4.4 Přihlášení po zahájení termínu (Otevřený bod č. 4)
* **Rozhodnutí (ADR-003):** Standardně platí pravidlo `term.date_from > today`; pokus o pozdní přihlášení vrátí `HTTP 400`. Pro domluvené výjimky má výhradně administrátor možnost zapnout `admin_override = True` s povinným textovým důvodem `admin_override_reason`, který se ukládá přímo k přihlášce pro zpětný audit. Samoobslužný endpoint `/registrations/self` vždy vynucuje `admin_override = False`.

### 4.5 Střídání více lektorů a jejich hodiny (Otevřený bod č. 5 & ADR-005)
* **Rozhodnutí:** Místo prostého cizího klíče `lecturer_id` na termínu používáme vazební tabulku `term_lecturers` s atributem `taught_hours`. Díky tomu se na delším kurzu mohou libovolně střídat 2 i více externistů a manažerský report (`GET /api/v1/reports/lecturer-hours`) přesně sčítá reálně odučené hodiny každého lektora.
* **Navíc (ADR-005):** `TermService.create()` kontroluje časový překryv intervalů `[date_from, date_to]` všech přiřazených lektorů a při kolizi operaci zamítne (`HTTP 400`).

---

## 5. REST API, webové rozhraní a uživatelské role

Aplikace poskytuje dokumentované REST API na `/docs` (Swagger UI) a webový dashboard na `/`.

### Přehled hlavních API endpointů (`/api/v1`)
| Skupina | Endpointy | Účel |
|---|---|---|
| **Autentizace** | `POST /auth/login` | Ověření e-mailu a hesla (Admin / Lektor / Student) |
| **Kurzy** | `GET /courses`, `POST /courses` | Katalog vzdělávacích kurzů |
| **Termíny** | `GET /terms`, `POST /terms`, `GET /terms/{id}` | Správa termínů, obsazenosti a přiřazení lektorů |
| **Studenti & Lektoři** | `GET/POST /students`, `GET/POST /lecturers` | Evidence osob s kontrolou unikátnosti e-mailu |
| **Přihlášky** | `POST /registrations`, `POST /registrations/self`, `POST /registrations/{id}/cancel`, `GET /registrations/term/{id}`, `GET /registrations/student/{id}` | Admin zápis, samoobslužný zápis studenta, zrušení s auto-posunem, přehledy |
| **Docházka** | `POST /attendance`, `GET /attendance/summary/{reg_id}` | Denní docházka a souhrn splnění limitu ≥ 70 % |
| **Osvědčení** | `POST /certificates/issue`, `GET /certificates/{number}` | Vystavení a čtení neměnného osvědčení |
| **Reporty** | `GET /reports/occupancy`, `GET /reports/lecturer-hours`, `GET /reports/multi-course-students` | Manažerské statistiky + podklady pro CSV export |

### Uživatelské role a oddělení oprávnění (ADR-007, ADR-008)
* **Nepřihlášený návštěvník:** Vidí pouze veřejný *Katalog kurzů* a *Termíny a kapacity*; může odeslat samoobslužnou přihlášku na kurz nebo se přihlásit.
* **Student:** Vidí katalog, termíny a vlastní záložku *Moje přihlášky a osvědčení* (stav přihlášky, pořadí v pořadníku, docházka, tisk osvědčení, možnost odhlásit se). Nemá přístup ke správě ani reportům.
* **Lektor:** Vidí pouze *Moje termíny* (vyfiltrované podle přiřazení v `term_lecturers`) a *Docházka a osvědčení* pro své studenty.
* **Administrátor:** Kompletní správa kurzů, termínů, přihlášek (včetně auditovaných výjimek po zahájení), docházky, osvědčení, manažerských reportů a CSV exportů.

---

## 6. Testování a ověření kvality

Všechna klíčová obchodní pravidla i kompletní uživatelský průchod aplikací jsou pokryty automatizovanými testy v `pytest` (běžícími v izolované in-memory SQLite databázi lokálně i uvnitř Docker kontejneru).

| Soubor | Test | Co ověřuje |
|---|---|---|
| `tests/test_business_rules.py` | `test_rule_capacity_and_fifo_queue` | Striktní limit kapacity a FIFO pořadí náhradníků |
| `tests/test_business_rules.py` | `test_rule_cancellation_audit_and_auto_promote` | Auditní uchování zrušené přihlášky a auto-posun náhradníka č. 1 |
| `tests/test_business_rules.py` | `test_rule_no_concurrent_registration_same_course` | Zákaz dvou aktivních přihlášek na stejný kurz |
| `tests/test_business_rules.py` | `test_rule_certificate_issuing_and_immutability` | Limit ≥ 70 % docházky, unikátní číslo a neměnnost certifikátu |
| `tests/test_business_rules.py` | `test_rule_late_registration_admin_override` | Blokace pozdního zápisu a auditovaná výjimka admina |
| `tests/test_business_rules.py` | `test_rule_lecturer_schedule_conflict` | Zákaz časového překryvu výuky u téhož lektora |
| `tests/test_business_rules.py` | `test_rule_student_self_registration_and_history` | Samoobslužný zápis nového/existujícího studenta a jeho historie |
| `tests/test_business_rules.py` | `test_auth_login_roles_and_rejection` | Přihlášení všech 3 rolí a zamítnutí neplatného hesla (`401`) |
| `tests/test_e2e_user_flows.py` | `test_full_user_journey_e2e` | Kompletní HTTP end-to-end scénář se stejnými payloady jako `app.js` |

**Stav ověření:** 9/9 testů prochází (`pytest -v` lokálně i `docker compose exec app pytest -v`). Doplňkově je k dispozici interaktivní konzolový skript `python demo.py`, který v 8 krocích předvede celý životní cyklus kurzu nad izolovanou in-memory databází.

---

## 7. Nasazení, konfigurace a výhledová rozšiřitelnost

### Spuštění a bezpečnost konfigurace
* Celý systém se spouští jediným příkazem `docker compose up --build -d`.
* Startovací sekvence kontejneru `akademie_app` automaticky aplikuje migrace (`alembic upgrade head`), idempotentně vloží syntetická data (`python -m src.app.seed`) a spustí server `uvicorn`.
* Veškerá data v projektu jsou **výhradně syntetická**. Přihlašovací údaje a databázové proměnné se konfigurují přes `.env` dle šablony `.env.example`; samotný soubor `.env` je uveden v `.gitignore` a není verzován v Gitu.

### Připravenost na budoucí požadavky klienta
Architektura již nyní počítá s výhledovými požadavky zmíněnými klientem:
* **Fakturace:** Entita `Registration` drží vazbu na `Student`, `Term` (a přes něj `Course.price`) a jasný stavový model — napojení budoucí tabulky `Invoice` (`registration_id FK`) nevyžaduje změnu stávajících entit.
* **E-mailové notifikace:** Klíčové události (potvrzení přihlášky, povýšení z pořadníku, vydání osvědčení) jsou centralizovány v servisních metodách, kam lze bez zásahu do API vložit asynchronní `NotificationService`.
* **Výkazy pro akreditační orgány / ministerstvo:** Exporty do CSV s UTF-8 BOM (plně kompatibilní s českým MS Excel) jsou již připraveny v manažerských reportech a lze je snadno rozšířit o další šablony.

---

## 8. Metodika práce s AI asistentem

Vývoj probíhal inkrementálně v souladu s lokálními pravidly v `AGENTS.md`:
* Každé netriviální architektonické a produktové rozhodnutí bylo nejprve předloženo ve variantách (výhody/nevýhody/doporučení), explicitně schváleno vývojářem a zaznamenáno jako ADR v `README.md`.
* Každý funkční celek byl ihned ověřen automatizovanými testy a izolovaně commitnut (konvenční commity `feat:`, `fix:`, `docs:`, `chore:`).
* End-to-end testování v závěrečné fázi odhalilo a odstranilo nesoulady názvů polí mezi frontendem (`app.js`) a Pydantic schématy (docházka, reporty, stav osvědčení) i problém s cachováním statických souborů v prohlížeči.
