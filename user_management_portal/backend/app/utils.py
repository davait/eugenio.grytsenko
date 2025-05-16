"""
Utility functions and decorators for the User Management Portal.

This module provides validation functions and decorators for user data validation.
"""

import re
import logging
from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException

# Configure logging
logger = logging.getLogger(__name__)

# Valid department values
VALID_DEPARTMENTS = {'Tech', 'RRHH', 'Sales'}

def validate_email(email: str) -> bool:
    """
    Validate email format using regex pattern.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if email is valid, False otherwise
        
    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    try:
        # RFC 5322 compliant email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, email))
        logger.debug(f"Email validation for {email}: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Error validating email {email}: {str(e)}")
        return False

def validate_username(username: str) -> bool:
    """
    Validate username format (alphanumeric, 6-20 characters).
    
    Args:
        username (str): Username to validate
        
    Returns:
        bool: True if username is valid, False otherwise
        
    Example:
        >>> validate_username("validUser123")
        True
        >>> validate_username("short")
        False
    """
    try:
        # Check length and alphanumeric pattern
        is_valid = (
            len(username) >= 6 and
            len(username) <= 20 and
            bool(re.match(r'^[a-zA-Z0-9]+$', username))
        )
        logger.debug(f"Username validation for {username}: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Error validating username {username}: {str(e)}")
        return False

def validate_department(department: str) -> bool:
    """
    Validate department value.
    
    Args:
        department (str): Department to validate
        
    Returns:
        bool: True if department is valid, False otherwise
        
    Example:
        >>> validate_department("Tech")
        True
        >>> validate_department("Invalid")
        False
    """
    try:
        is_valid = department in VALID_DEPARTMENTS
        logger.debug(f"Department validation for {department}: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Error validating department {department}: {str(e)}")
        return False

def validate_user_data(func: Callable) -> Callable:
    """
    Decorator to validate user data before processing.
    
    Args:
        func (Callable): Function to decorate
        
    Returns:
        Callable: Decorated function
        
    Raises:
        HTTPException: If validation fails
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            # Extract email and username from kwargs
            email = kwargs.get('email')
            username = kwargs.get('username')
            department = kwargs.get('department')
            
            # Validate email
            if email and not validate_email(email):
                logger.warning(f"Invalid email format: {email}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid email format"
                )
            
            # Validate username
            if username and not validate_username(username):
                logger.warning(f"Invalid username format: {username}")
                raise HTTPException(
                    status_code=400,
                    detail="Username must be 6-20 characters long and contain only alphanumeric characters"
                )
            
            # Validate department
            if department and not validate_department(department):
                logger.warning(f"Invalid department: {department}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Department must be one of: {', '.join(VALID_DEPARTMENTS)}"
                )
            
            return func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in validation decorator: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error during validation"
            )
    return wrapper 