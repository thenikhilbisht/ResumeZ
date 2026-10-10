from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def create_database_engine():
    if not settings.database_url:
        return None

    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )


engine = create_database_engine()

SessionLocal = (
    sessionmaker(bind=engine, autoflush=False, autocommit=False)
    if engine is not None
    else None
)