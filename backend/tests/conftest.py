import pytest
from app.db.database import engine, Base, SessionLocal
from app.db.seed_data import seed_database

@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    """Initializes schema and seeds baseline publisher & trending data for tests."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
