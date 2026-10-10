from app.core.database import Base, SessionLocal, engine


def test_database_layer_loads_without_database_url():
    assert engine is None
    assert SessionLocal is None
    assert Base is not None