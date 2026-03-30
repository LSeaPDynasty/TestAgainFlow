"""
Database connection and session management
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.config import settings

logger = logging.getLogger(__name__)

# Validate database URL
def validate_database_url(url: str) -> str:
    """Validate and sanitize database URL"""
    if not url:
        raise ValueError("Database URL cannot be empty")

    # Check for dangerous patterns
    dangerous_patterns = [';', 'DROP', 'DELETE', 'TRUNCATE']
    url_upper = url.upper()
    if any(pattern in url_upper for pattern in dangerous_patterns):
        raise ValueError(f"Potentially dangerous database URL detected")

    return url

# Create database engine with connection pool
try:
    validated_url = validate_database_url(settings.database_url)

    engine = create_engine(
        validated_url,
        connect_args={"check_same_thread": False} if validated_url.startswith("sqlite") else {},
        echo=settings.debug,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,  # Recycle connections after 30 minutes
        pool_pre_ping=True,  # Verify connections before using
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Get database session with proper error handling
    Usage in FastAPI:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)
