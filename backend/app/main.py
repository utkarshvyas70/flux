from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter


app = FastAPI(
    title="Flux API",
    description="Version control system for LLM prompts",
    version="0.1.0",
)

origins = [
    "http://localhost:3000",
    "https://flux-app-lilac.vercel.app",
    "https://flux-ctwk8km65-utkarshvyas70s-projects.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        },
    )


def run_migrations():
    try:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("✓ Migrations applied")
    except Exception as e:
        print(f"Migration error: {e}")


def run_seed():
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        db = SessionLocal()
        existing = db.query(User).filter(User.email == "demo@flux.dev").first()
        db.close()
        if not existing:
            import subprocess
            subprocess.run(["python", "seed_demo.py"], check=True)
            print("✓ Demo data seeded")
        else:
            print("✓ Demo data exists")
    except Exception as e:
        print(f"Seed error: {e}")


@app.on_event("startup")
async def startup_event():
    run_migrations()
    run_seed()


from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.workspace import router as workspaces_router
from app.api.repository import router as repositories_router
from app.api.versions import router as versions_router
from app.api.versions import router2 as versions_router2
from app.api.evals import router as evals_router
from app.api.diff import router as diff_router
from app.api.playground import router as playground_router
from app.api.advisor import router as advisor_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(repositories_router)
app.include_router(versions_router)
app.include_router(versions_router2)
app.include_router(evals_router)
app.include_router(diff_router)
app.include_router(playground_router)
app.include_router(advisor_router)

@app.get("/")
def root():
    return {"message": "Flux API is running", "docs": "/docs", "health": "/health"}