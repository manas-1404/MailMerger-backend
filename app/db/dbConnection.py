from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.utils.config import settings

engine = create_engine(settings.DB_CONNECTION_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """
    Dependency to get a database session.
    This function can be used in FastAPI routes to get a session for database operations.
    """
    db = SessionLocal()
    try:
        yield db

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()