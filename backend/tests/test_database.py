
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine


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

    from app.core.database import check_database_connection

    assert check_database_connection() is True


def test_resumes_table_is_registered():
    from app.models import Resume
    from app.core.database import Base

    assert Resume.__tablename__ == "resumes"
    assert "resumes" in Base.metadata.tables
