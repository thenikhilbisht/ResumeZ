
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def create_database_engine():
    if not settings.database_url:
        return None

    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"timeout": 15},
    )


engine = create_database_engine()

SessionLocal = (
    sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    if engine is not None
    else None
)


def check_database_connection() -> bool:
    if engine is None:
        return False

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True


def get_db():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured.")

    db: Session = SessionLocal()

    try:
        yield db
    finally:
        db.close()
