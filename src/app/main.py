import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from src.app.core.config import settings
from src.app.core.database import engine, Base
from src.app.api.v1.endpoints import (
    courses,
    terms,
    lecturers,
    students,
    registrations,
    attendance,
    certificates,
    reports
)

# Inicializace schématu je plně řízena verzovanými migracemi Alembic (alembic upgrade head)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=r"""
    ## Informační systém pro vzdělávací centrum (Akademie Trutnov)
    Semestrální projekt pro předmět **Pokročilé programování (PPRO)** na FIM UHK.
    
    ### Klíčová předváděná pravidla:
    * **Nepřekročitelná kapacita termínu:** Striktní kontrola maximálního počtu účastníků.
    * **FIFO pořadník (Waiting list):** Automatické zařazení náhradníků s garantovaným pořadím.
    * **Automatický posun:** Při zrušení registrace uvolněné místo automaticky obsadí první náhradník z pořadníku.
    * **Audit zrušených přihlášek:** Přihlášky se fyzicky nemažou, slouží k auditu.
    * **Unikátní neměnná osvědčení:** Generování čísel osvědčení při splnění $\ge 70\ \%$ docházky a schválení lektorem.
    * **Statistické přehledy:** Vytížení kapacit, hodiny lektorů a vícekurzoví studenti.
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
def root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["Systém"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

api_prefix = settings.API_V1_STR
app.include_router(courses.router, prefix=api_prefix)
app.include_router(terms.router, prefix=api_prefix)
app.include_router(lecturers.router, prefix=api_prefix)
app.include_router(students.router, prefix=api_prefix)
app.include_router(registrations.router, prefix=api_prefix)
app.include_router(attendance.router, prefix=api_prefix)
app.include_router(certificates.router, prefix=api_prefix)
app.include_router(reports.router, prefix=api_prefix)
