"""FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

OpenAPI docs are auto-generated at:
    GET /docs       (Swagger UI)
    GET /redoc      (Redoc UI)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.database import Base, engine
from .routes import auth, users, categories, complaints, notifications, dashboard


# Auto-create tables on first run. For production, use Alembic migrations.
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Phase 1 capstone — REST API for managing the customer complaint "
        "lifecycle: registration, assignment, SLA tracking, escalation, "
        "resolution, feedback, and analytics."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# CORS so the React dev server (localhost:5173) can talk to the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount routers
for r in (auth, users, categories, complaints, notifications, dashboard):
    app.include_router(r.router, prefix=settings.API_PREFIX)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "code": settings.PROJECT_CODE,
        "version": settings.VERSION,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "healthy"}
