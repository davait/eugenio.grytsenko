"""
Database configuration module for the User Management Portal.

This module handles the database connection setup using SQLAlchemy,
including engine creation, session management, and database URL configuration.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# SQLite database URL configuration
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./user_management.db"
)
logger.info(f"Database URL configured: {SQLALCHEMY_DATABASE_URL}")

# Create SQLAlchemy engine with SQLite-specific configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=True  # Enable SQL query logging
)
logger.info("SQLAlchemy engine created")

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.info("SessionLocal class created")

# Create Base class for declarative models
Base = declarative_base()
logger.info("Base class for declarative models created")

def get_db():
    """
    Dependency function to get database session.
    
    Yields:
        Session: A SQLAlchemy database session.
        
    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        logger.debug("Database session created")
        yield db
    finally:
        logger.debug("Database session closed")
        db.close()
