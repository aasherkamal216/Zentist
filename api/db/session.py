from sqlmodel import create_engine, Session, SQLModel
from core.config import get_settings

settings = get_settings()

engine = create_engine(
    url=settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    connect_args=settings.DB_CONNECT_ARGS,
)

def get_db_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    """
    Utility function to create database tables.
    """
    SQLModel.metadata.create_all(engine)