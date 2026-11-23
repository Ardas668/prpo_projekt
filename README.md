# Akademie Trutnov – Informační systém pro správu kurzů (PPRO)

Tento repozitář obsahuje semestrální projekt pro předmět **Pokročilé programování (PPRO)** na Fakultě informatiky a managementu Univerzity Hradec Králové (ZS 2026/2027).

Projekt realizuje **Variantu C: Kurzy vzdělávacího centra**.

> 📄 **Kompletní technická dokumentace** (architektura, ER a sekvenční diagramy, rozbor FIFO pořadníku a dokončení kurzu, API přehled a metodika testování): **[docs/technicka_dokumentace.md](./docs/technicka_dokumentace.md)**

---

## 1. Kontext a zadání klienta

* **Klient:** Ing. Lucie Bartošová, Akademie Trutnov
* **Charakteristika organizace:** Vzdělávací centrum poskytující rekvalifikační a firemní kurzy (cca 40 běhů ročně). Lektoři jsou externisté.

### 1.1 Současný stav („Jak to mají dnes“)
* **Příjem přihlášek:** Přihlášky přicházejí z webového formuláře do e-mailu a pověřený pracovník je ručně přepisuje do tabulkového procesoru (samostatná záložka pro každý kurz).
* **Řízení kapacit:** Obsazenost se kontroluje pouze lidským okem. Pořadník náhradníků je řešen formou poznámek tužkou pod seznamem.
* **Osvědčení o absolvování:** Vypisují se ručně v textovém editoru (MS Word). Evidenční čísla osvědčení se přidělují odhadem podle předchozích ročních záznamů, což již v minulosti vedlo k duplicitnímu přidělení stejného čísla.
* **Hlavní slabina:** Při odřeknutí přihlášeného účastníka na poslední chvíli vzniká chaos – chybí přehledný mechanismus, koho z pořadníku náhradníků oslovit.

---

## 2. Funkční požadavky („Co klient chce“)

1. **Správa kurzů (katalog):**
   * Evidence základních údajů kurzu: název, anotace (popis), rozsah v hodinách, cena a příznak akreditace (zda je kurz akreditovaný).
2. **Termíny kurzů:**
   * Kurz se opakuje několikrát do roka v různých termínech.
   * Termín má definované datum začátku a konce (`od` – `do`), místo konání a maximální kapacitu.
   * Kapacita téhož kurzu se liší v závislosti na přidělené učebně / lokalitě.
3. **Lektoři a jejich přiřazení k termínům:**
   * Evidence lektorů (externistů).
   * Jeden lektor může vést více termínů.
   * U delších kurzů je vyžadována možnost střídání dvou lektorů na jednom termínu.
4. **Přihlášky studentů na termíny:**
   * Evidence studentů / účastníků.
   * Vazba student ↔ termín (jeden student navštěvuje více kurzů/termínů, na jednom termínu je zapsáno více studentů).
5. **Kapacita a pořadník (Waiting list):**
   * Pokud je kapacita termínu naplněna, další přihlašující se zájemce je zařazen do pořadníku s přesným uchováním pořadí (FIFO).
   * Při uvolnění místa v termínu (odhlášení zapsaného studenta) musí systém jasně indikovat, který zájemce z pořadníku je na řadě.
6. **Evidence docházky:**
   * U vícedenních termínů se eviduje účast každého studenta pro každý konkrétní den výuky.
7. **Dokončení kurzu a vydání osvědčení:**
   * Na konci termínu se eviduje seznam absolventů, kteří kurz úspěšně dokončili.
   * Pro každého absolventa se vystaví osvědčení s jedinečným evidenčním číslem a datem vystavení. Číslo osvědčení se nesmí nikdy opakovat.
8. **Přehledy a manažerské statistiky:**
   * Přehled naplněnosti jednotlivých termínů.
   * Celkový počet odučených hodin za jednotlivé lektory.
   * Přehled studentů, kteří se v daném roce přihlásili na více než jeden kurz.

---

## 3. Obchodní pravidla („Na čem klient trvá – striktně vynutit systémem“)

Systém musí aplikačně i databázově garantovat tato pravidla:

1. **Striktní limit kapacity:** Kapacitu termínu nelze za žádných okolností překročit (ani ručně, ani omylem).
2. **Nepřeskakovatelný pořadník:** Pořadí zájemců v pořadníku musí být striktně dodrženo, zájemce nelze svévolně předbíhat.
3. **Integrita osvědčení:** Číslo osvědčení je globálně unikátní. Již jednou vydané a evidované osvědčení je neměnné (nelze zpětně modifikovat identifikační údaje certifikátu).
4. **Auditní stopa přihlášek:** Zrušená přihláška se fyzicky nemaže, zůstává v systému plně dohledatelná (pro řešení sporných situací a reklamací účastníků).

---

## 4. Výhledová přání klienta („Co klient prohodil mimochodem“)

Tyto body nejsou součástí povinného MVP, ale architektura a doménový model s nimi musí počítat bez nutnosti kompletního přepracování:
* **Fakturace:** V první fázi se neimplementuje, avšak stavový model přihlášky a studenta musí umožnit budoucí napojení plateb a fakturace.
* **Ergonomie a přístupnost:** Rozhraní musí být přehledné a intuitivní i pro starší a méně technicky zdatné lektory.
* **E-mailové notifikace:** Automatické odesílání potvrzení přihlášky, výzev z pořadníku a potvrzení o dokončení.
* **Výkazy pro státní orgány:** Možnost exportu podkladů pro akreditační orgány / ministerstvo.

---

## 5. Otevřené body klienta a návrhová úskalí

Zadání explicitně identifikuje místa, kde klient nemá ujasněné procesy a kde se láme architektonický návrh:

| # | Otevřený bod | Podstata dilematu | Návrhové řešení k rozhodnutí |
|---|---|---|---|
| **1** | **Pravidlo pro dokončení kurzu** | Klient jednou uvádí fixní limit (70 % docházky), jindy subjektivní posouzení lektora. | Zvolit a zkombinovat metriku: buď automatické splnění docházky jako prerekvizita + formální schválení lektorem, nebo striktní 70% docházka. |
| **2** | **Posun náhradníka z pořadníku** | Není jasné, zda se první náhradník propíše na volné místo automaticky, nebo zda je vyžadováno potvrzení administrátorem / účastníkem (pro případ, že už nemá zájem). | Definovat stavový diagram místa v pořadníku (automatická rezervace s časovým limitem na potvrzení vs. manuální krok administrátora). |
| **3** | **Souběžné termíny téhož kurzu** | Může se student přihlásit na dva různé termíny stejného kurzu současně? | Definovat validační pravidlo na úrovni přihlášky (povolit pouze jeden aktivní termín na kurz na studenta, nebo povolit bez omezení). |
| **4** | **Přihlášení po zahájení termínu** | Obecně zakázáno, ale klient připouští neformální výjimky („když je to domluvené“). | Explicitní právo role administrátora povolit zápis po zahájení s auditním záznamem důvodu výjimky. |
| **5** | **Rozdělení hodin při střídání lektorů** | Klient chce evidovat střídání dvou lektorů na termínu, ale statistiku hodin požaduje „na lektora termínu“. | Modelovat vazbu lektora na konkrétní dny/výukové bloky termínu, aby bylo možné spočítat reálně odučené hodiny každého z nich. |

---

## 6. Společné technické minimum projektu

V souladu s požadavky semestrální práce:
* **Třívrstvá architektura:** Striktní oddělení vrstev s jednosměrnými závislostmi (Prezentační / API vrstva → Aplikační / Doménová vrstva → Datová / Infrastrukturní vrstva).
* **Relační databáze v Dockeru:** Využití relačního DBMS s verzovanými migracemi schématu.
* **Doménový model:** Minimálně 5 plnohodnotných entit a alespoň jedna vazba M:N.
* **Testy:** Automatizované testy ověřující klíčová obchodní pravidla (kapacity, pořadník, neměnnost osvědčení).
* **Jednoduché spuštění:** Celá aplikace i databáze musí být spustitelná jediným příkazem `docker compose up`.
* **Data:** Výhradně syntetická testovací data (žádné reálné osobní údaje, žádná tajemství ani hesla v gitu).

---

## 7. Rozhodnutí (Architecture & Business Decision Log)

Tato sekce průběžně zaznamenává všechna klíčová věcná a architektonická rozhodnutí dohodnutá v rámci realizace projektu.

### Záznamy rozhodnutí

#### ADR-001: Volba zadání a základního rozsahu
* **Datum:** 2026-10-05
* **Stav:** Schváleno
* **Kontext:** Výběr ze čtyř nabízených variant semestrálního projektu PPRO.
* **Rozhodnutí:** Realizovat **Variantu C – Kurzy vzdělávacího centra (Akademie Trutnov)**.
* **Důsledky:** Zaměření na správu kurzů, termínů, lektorů, docházky, nepřekročitelných kapacit, FIFO pořadníku a certifikátů.

#### ADR-002: Volba technologického stacku pro DEMO a realizaci
* **Datum:** 2026-10-05
* **Stav:** Schváleno
* **Kontext:** Výběr programovacího jazyka a frameworku pro splnění požadavků PPRO.
* **Rozhodnutí:** Realizovat projekt v jazyce **Python** ve variantě A: **FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL + Docker Compose**.
* **Důsledky:**
  * Třívrstvá architektura: Prezentační vrstva (FastAPI routery, Pydantic schémata, Swagger UI), Byznys vrstva (Service třídy s doménovými pravidly), Datová vrstva (SQLAlchemy ORM + repozitáře).
  * Verzované databázové migrace přes Alembic.
  * Interaktivní dokumentace a demo rozhraní na `/docs` (Swagger UI).
  * Běh kompletního systému (databáze + migrace + backend) zajištěn přes `docker compose up`.

#### ADR-003: Vyřešení otevřených bodů klienta a návrh doménového modelu
* **Datum:** 2026-10-05
* **Stav:** Schváleno
* **Kontext:** Zadání klienta obsahuje 5 otevřených bodů a neurčených procesních detailů. Bylo nutné stanovit jednoznačná pravidla před implementací.
* **Rozhodnutí:**
  1. *Podmínka dokončení kurzu:* Docházka studenta $\ge 70\ \%$ a současně schválení lektorem/administrátorem před vystavením osvědčení.
  2. *Posun z FIFO pořadníku:* Automatický posun prvního náhradníka do stavu `CONFIRMED` při uvolnění kapacity, s auditním záznamem posunu.
  3. *Souběh termínů téhož kurzu:* Student nesmí mít více než jednu aktivní přihlášku (`CONFIRMED` nebo `WAITING_LIST`) na stejný kurz současně (ochrana proti spekulativnímu blokování kapacit).
  4. *Přihlášení po zahájení kurzu:* Standardně blokováno; povoleno pouze administrátorovi přes explicitní parametr s povinným uvedením důvodu výjimky.
  5. *Rozpad hodin při střídání lektorů:* Využití vazební tabulky `TermLecturer` s explicitní evidencí odučených hodin (`taught_hours`) pro každého lektora v termínu.
* **Důsledky:** Doménový model obsahuje 7 tabulek/entit: `Course`, `Term`, `Lecturer`, `TermLecturer` (M:N), `Student`, `Registration` (M:N), `Attendance` a `Certificate`.

#### ADR-004: Implementace grafického rozhraní (Frontend UI Dashboard)
* **Datum:** 2026-10-19
* **Stav:** Schváleno
* **Kontext:** Uživatel požaduje vizuální prezentaci informačního systému na kořenové adrese (`http://localhost:8000/`) namísto pouhého přesměrování na technickou Swagger UI dokumentaci.
* **Rozhodnutí:** Realizovat moderní Single-Page Dashboard postavený na HTML5, Vanilla CSS (design tokens, dark/light podpora, mikroanimace, glassmorphism) a JavaScriptu ES6, servírovaný přímo aplikací FastAPI jako statická aplikace.
* **Důsledky:**
  * Kořenová adresa `/` otevírá plnohodnotné rozhraní Akademie Trutnov (katalog kurzů, termíny s kapacitami, FIFO pořadník s demonstrací automatického posunu při zrušení přihlášky, docházka, vydávání osvědčení a manažerské reporty).
  * API dokumentace zůstává nedotčena a dostupná na `/docs` a `/redoc`.
  * Není nutné přidávat Node.js ani další servisní kontejner do `docker-compose.yml`.

#### ADR-005: Validace časových kolizí lektorů
* **Datum:** 2026-11-23
* **Stav:** Schváleno
* **Kontext:** Zadání klienta vyžaduje evidenci externích lektorů a střídání lektorů na termínech. Bylo nutné zajistit, aby externí lektor nebyl v systému omylem přiřazen k výuce dvou různých termínů/kurzů ve stejném časovém intervalu.
* **Rozhodnutí:** V servisní vrstvě (`TermService`) striktně validovat překryv termínů při přiřazení lektora. Pokud lektor již učí na termínu, jehož interval `[date_from, date_to]` koliduje s nově přiřazovaným termínem, systém operaci zamítne s chybovým kódem HTTP 400.
* **Důsledky:**
  * Ochrana proti nereálnému rozvrhování externistů.
  * Pokryto automatizovaným integračním testem `test_rule_lecturer_schedule_conflict`.

---

#### ADR-006: Rozšíření webové správy a vizuální styl vzdělávacího centra
* **Datum:** 2026-11-23
* **Stav:** Schváleno
* **Kontext:** Původní technologický tmavý vzhled neodpovídal charakteru regionálního vzdělávacího centra a v rozhraní chyběla možnost zakládat nové termíny s lektory a studenty přímo z webu.
* **Rozhodnutí:**
  1. Zvolit přívětivější, přístupný styl inspirovaný krkonošským regionem (světlý podklad, smrková zeleň `#0f766e`, jemné jantarové akcenty).
  2. Doplnit formuláře pro zakládání termínů s dynamickým přiřazením lektorů a rozpadem hodin, modal pro rychlé vytvoření studenta a export reportů do formátu CSV s UTF-8 BOM pro MS Excel.
* **Důsledky:** Plná soběstačnost webového rozhraní pro správu centra, přehledné manažerské výkazy.

---

#### ADR-007: Profilový přepínač rolí a samoobslužný zápis studentů
* **Datum:** 2026-11-23
* **Stav:** Schváleno
* **Kontext:** Podle zadání se účastníci na kurzy přihlašují sami (dříve formulářem do e-mailu) a v systému vystupují tři role: Administrátor, Lektor a Student. Pro účely semestrálního projektu je prioritou snadná demonstrovatelnost všech rolí bez zbytečné režie s JWT/hesly.
* **Rozhodnutí:**
  1. Zobrazit v hlavičce jednoduchý přepínač profilu (`Administrátor`, `Lektor` s výběrem lektora, `Student / Zájemce` s výběrem studenta nebo režimem nového zájemce).
  2. Přidat endpoint `POST /api/v1/registrations/self` (samoobslužná přihláška podle jména a e-mailu; neznámý e-mail automaticky založí studenta, existující profil spáruje) a `GET /api/v1/registrations/student/{student_id}` pro studentský přehled *Moje přihlášky a osvědčení*.
  3. Omezit viditelnost záložek a akcí podle aktivní role (Lektor vidí své termíny a docházku, Student katalog + své přihlášky/osvědčení, Administrátor kompletní správu).
* **Důsledky:** Aplikace věrně pokrývá všechny tři role ze zadání bez ukládání hesel v repozitáři (`.env` zůstává v `.gitignore`). Pokryto testem `test_rule_student_self_registration_and_history`.

---

#### ADR-008: Jednoduchý login podle rolí a zákaz cachování statických souborů
* **Datum:** 2026-11-23
* **Stav:** Schváleno
* **Kontext:** Otevřený přepínač rolí v hlavičce umožňoval libovolně přepnout na administrátora bez autentizace. Zároveň cachování statického `app.js` v prohlížeči způsobovalo načítání zastaralého rozhraní.
* **Rozhodnutí:**
  1. Nahradit přepínač rolí jednoduchým přihlašovacím formulářem (`POST /api/v1/auth/login`) s e-mailem a heslem; výchozí stav je nepřihlášený návštěvník (vidí jen veřejný katalog a termíny).
  2. Přihlašovací hesla spravovat přes `.env` (šablona v `.env.example`, lokální `.env` je v `.gitignore`).
  3. Přidat HTTP middleware nastavující `Cache-Control: no-store` pro `/` a `/static/*` a verzovací parametr `?v=...` v HTML.
* **Důsledky:** Přísné oddělení oprávnění pro Návštěvníka, Studenta, Lektora a Administrátora, čisté testování v prohlížeči bez problémů s cache. Pokryto testem `test_auth_login_roles_and_rejection`.

---

## 8. Uživatelská příručka a pokyny pro spuštění

Systém je plně kontejnerizován a připraven pro okamžité spuštění a hodnocení.

### 8.1 Spuštění aplikace v Dockeru (doporučeno)

Pro spuštění celého systému (PostgreSQL databáze + migrace schématu + backend + webové UI) stačí jediný příkaz v kořenovém adresáři:

```bash
docker compose up --build -d
```

Po spuštění jsou k dispozici tyto adresy:
* **Webový Dashboard Akademie Trutnov:** [http://localhost:8000/](http://localhost:8000/)
* **Interaktivní API dokumentace (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Alternativní dokumentace (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 8.1.1 Přihlášení a testovací role
Výchozí hesla pro lokální spuštění jsou konfigurovatelná v lokálním souboru `.env` (viz šablona `.env.example`; soubor `.env` je v `.gitignore` a není součástí repozitáře):
* **Administrátor:** `admin@akademietrutnov.cz` (heslo `ADMIN_PASSWORD` z `.env`, výchozí `admin123`) – plná správa kurzů, termínů, přihlášek, docházky, osvědčení a reportů.
* **Lektor:** např. `petr.novak@akademietrutnov.cz` nebo `jana.svobodova@akademietrutnov.cz` (heslo `LECTURER_DEMO_PASSWORD`, výchozí `lektor123`) – pouze vlastní přidělené termíny a jejich docházka/osvědčení.
* **Student:** např. `martin.dvorak@example.cz` nebo `alena.cerna@example.cz` (heslo `STUDENT_DEMO_PASSWORD`, výchozí `student123`) – katalog kurzů, samoobslužný zápis a záložka *Moje přihlášky a osvědčení*.

Zastavení aplikace:
```bash
docker compose down
```

### 8.2 Spuštění automatizovaných testů

Všechna klíčová obchodní pravidla jsou plně pokryta automatizovanými testy (SQLite in-memory, běh v řádu zlomků sekundy):

**Spuštění v běžícím Docker kontejneru:**
```bash
docker compose exec app pytest
```

**Lokální spuštění přes Python virtuální prostředí:**
```bash
.\.venv\Scripts\pytest -v
```

### 8.3 Spuštění uceleného konzolového dema

Pro rychlé automatické předvedení všech 8 kroků životního cyklu kurzu a ověření obchodních pravidel:

```bash
python demo.py
```
*(Skript běží v izolované in-memory databázi, takže neovlivní data v běžícím PostgreSQL kontejneru.)*

### 8.4 Přehled ověřených obchodních pravidel a mapování v kódu

| Pravidlo | Popis chování systému | Kde je implementováno | Automatizovaný test |
|---|---|---|---|
| **Striktní limit kapacity** | Kapacitu termínu nelze překročit ani omylem. | `RegistrationService.register_student` | `test_rule_capacity_and_fifo_queue` |
| **FIFO pořadník náhradníků** | Po naplnění kapacity je zájemce zařazen na konec fronty (#1, #2...). | `RegistrationService.register_student` | `test_rule_capacity_and_fifo_queue` |
| **Automatický posun z pořadníku** | Při odhlášení zapsaného studenta se první náhradník automaticky posune na potvrzené místo. | `RegistrationService.cancel_registration` | `test_rule_cancellation_audit_and_auto_promote` |
| **Auditní stopa přihlášek** | Zrušená přihláška se fyzicky nemaže (`CANCELLED`, čas zrušení). | `RegistrationService.cancel_registration` | `test_rule_cancellation_audit_and_auto_promote` |
| **Zákaz spekulativního souběhu** | Student nesmí mít 2 aktivní přihlášky na stejný kurz současně. | `RegistrationService.register_student` | `test_rule_no_concurrent_registration_same_course` |
| **Zápis po zahájení termínu** | Standardně zakázán (400); povolen pouze administrátorovi s povinným důvodem. | `RegistrationService.register_student` | `test_rule_late_registration_admin_override` |
| **Časová kolize lektorů** | Lektor nemůže učit 2 termíny, které se časově překrývají. | `TermService.create` | `test_rule_lecturer_schedule_conflict` |
| **Podmínka osvědčení** | Vyžaduje $\ge 70\ \%$ docházky a formální schválení lektorem. | `CertificateService.issue_certificate` | `test_rule_certificate_issuing_and_immutability` |
| **Neměnnost osvědčení** | Číslo je unikátní (`TRU-YYYY-XXXXX`), jednou vydané osvědčení nelze přepsat. | `CertificateService.issue_certificate` | `test_rule_certificate_issuing_and_immutability` |

---

*(Dokumentace semestrálního projektu Pokročilé programování – FIM UHK)*

