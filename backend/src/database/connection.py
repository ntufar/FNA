"""
Database connection and session management for FNA Platform.

Provides SQLAlchemy engine, session factory, and dependency injection
for FastAPI applications.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from ..core.config import get_settings

logger = logging.getLogger(__name__)

# Global variables for engine and session factory
engine: Engine = None
SessionLocal: sessionmaker = None


def create_database_engine() -> Engine:
    """
    Create SQLAlchemy engine with optimized connection pool settings.
    
    Returns:
        Engine: Configured SQLAlchemy engine
    """
    settings = get_settings()
    
    engine_config = {
        "url": settings.database_url,
        "poolclass": QueuePool,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 3600,  # 1 hour
        "echo": settings.debug,  # Log SQL queries in debug mode
    }
    
    try:
        db_engine = create_engine(**engine_config)
        
        # Test connection
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully")
            
        return db_engine
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


def init_database():
    """
    Initialize database engine and session factory.
    Call this once at application startup.
    """
    global engine, SessionLocal
    
    if engine is None:
        logger.info("Initializing database connection...")
        engine = create_database_engine()
        
        # Create session factory
        SessionLocal = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
        )
        
        # Add event listeners for connection management
        _setup_connection_events(engine)
        
        logger.info("Database initialization completed")


def get_engine() -> Engine:
    """
    Get the database engine instance.
    
    Returns:
        Engine: SQLAlchemy engine instance
        
    Raises:
        RuntimeError: If database hasn't been initialized
    """
    global engine
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return engine


def _setup_connection_events(db_engine: Engine):
    """Setup database connection event listeners for monitoring and optimization."""
    
    @event.listens_for(db_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Configure PostgreSQL connection settings."""
        if "postgresql" in str(db_engine.url):
            with dbapi_connection.cursor() as cursor:
                # Set application name for connection identification
                cursor.execute("SET application_name = 'fna-platform'")
                # Optimize for read-heavy workloads
                cursor.execute("SET default_statistics_target = 100")
    
    @event.listens_for(db_engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        """Log connection checkout for monitoring."""
        logger.debug("Database connection checked out from pool")
    
    @event.listens_for(db_engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        """Log connection return for monitoring."""
        logger.debug("Database connection returned to pool")


def get_db_session() -> Session:
    """
    Create a new database session.
    Use this for dependency injection in FastAPI routes.
    
    Returns:
        Session: SQLAlchemy session instance
        
    Raises:
        RuntimeError: If database not initialized
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    return SessionLocal()


@contextmanager
def get_db_session_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Automatically handles session lifecycle and error handling.
    
    Yields:
        Session: SQLAlchemy session instance
        
    Example:
        with get_db_session_context() as session:
            user = session.query(User).filter(User.email == email).first()
            session.commit()
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error in database session: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def close_database():
    """
    Close database engine and clean up connections.
    Call this at application shutdown.
    """
    global engine
    
    if engine:
        logger.info("Closing database connections...")
        engine.dispose()
        engine = None
        logger.info("Database connections closed")


# FastAPI dependency for route injection
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to provide database session to routes.
    
    Yields:
        Session: SQLAlchemy session instance
        
    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    with get_db_session_context() as session:
        yield session


# Health check function
def check_database_health() -> dict:
    """
    Check database connectivity and pool status.
    
    Returns:
        dict: Health status information
    """
    if engine is None:
        return {
            "status": "error",
            "message": "Database engine not initialized"
        }
    
    try:
        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT version()"))
            db_version = result.scalar()
            
            # Get pool status
            pool = engine.pool
            pool_status = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }
            
            return {
                "status": "healthy",
                "database_version": db_version,
                "pool_status": pool_status,
                "connection_url": str(engine.url).replace(engine.url.password or "", "***")
            }
            
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# Transaction utilities
@contextmanager
def atomic_transaction() -> Generator[Session, None, None]:
    """
    Context manager for atomic database transactions.
    Automatically rolls back on any exception.
    
    Yields:
        Session: SQLAlchemy session instance
        
    Example:
        with atomic_transaction() as session:
            user = User(email="test@example.com")
            session.add(user)
            # Automatically commits on success, rolls back on exception
    """
    with get_db_session_context() as session:
        try:
            yield session
            # Commit is handled by get_db_session_context
        except Exception as e:
            # Rollback is handled by get_db_session_context
            logger.error(f"Transaction failed, rolled back: {e}")
            raise
