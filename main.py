from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from pydantic import BaseModel

from core.config import get_settings
from api.db.session import create_db_and_tables
from api.routers import chat, appointments

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    print(f"INFO:     Starting up {settings.APP_NAME} v{settings.APP_VERSION}...")
    print("INFO:     Database tables checked/created.")
    create_db_and_tables()
    yield
    # On shutdown
    print(f"INFO:     Shutting down {settings.APP_NAME}...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AppConfig(BaseModel):
    supabase_url: str
    supabase_anon_key: str

config_router = APIRouter()

@config_router.get("/config", response_model=AppConfig)
def get_app_config():
    """Provides public-facing configuration variables to the frontend."""
    return AppConfig(
        supabase_url=settings.SUPABASE_URL,
        supabase_anon_key=settings.SUPABASE_KEY
    )

# --- API Routers ---
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(appointments.router, prefix="/api/v1/appointments", tags=["Appointments"])
app.include_router(config_router, prefix="/api/v1", tags=["Configuration"])

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}