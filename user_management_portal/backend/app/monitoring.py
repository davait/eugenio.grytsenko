"""
Monitoring module for the User Management Portal.

This module provides a simple health check endpoint for monitoring
the application's status.
"""

import logging
import time
import platform
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/monitoring",
    tags=["monitoring"],
    responses={404: {"description": "Not found"}},
)

def check_database_health(db: Session) -> Dict[str, Any]:
    """
    Check database health by executing a simple query.
    
    Args:
        db: Database session
        
    Returns:
        Dict[str, Any]: Database health information
    """
    try:
        start_time = time.time()
        result = db.execute(text("SELECT 1")).scalar()
        query_time = time.time() - start_time
        
        return {
            "status": "healthy" if result == 1 else "unhealthy",
            "query_time_seconds": round(query_time, 3)
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint that returns the status of various components.
    
    Args:
        db: Database session
        
    Returns:
        Dict[str, Any]: Health check information
    """
    try:
        # Check database health
        db_health = check_database_health(db)
        
        # Get system info
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        }
        
        return {
            "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.6.0",
            "components": {
                "database": db_health,
                "system": system_info
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
