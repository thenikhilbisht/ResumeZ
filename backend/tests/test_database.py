
from sqlalchemy import text

from app.core.config import settings
from app.core.database import (
    Base,
    SessionLocal,
    check_database_connection,
    engine,
    get_db,
)
from app.models import Resume


def test_database_layer_initializes():
    assert Base is not None

    if settings.database_url:
        assert engine is not None
        assert SessionLocal is not None
    else:
        assert engine is None
        assert SessionLocal is None


def test_database_connection():
    if not settings.database_url:
        return

    assert check_database_connection() is True


def test_resumes_table_is_registered():
    assert Resume.__tablename__ == "resumes"
    assert "resumes" in Base.metadata.tables


def test_get_db_session_lifecycle():
    assert SessionLocal is not None

    generator = get_db()
    db = next(generator)

    try:
        result = db.execute(text("SELECT 1")).scalar_one()
        assert result == 1
    finally:
        generator.close()
