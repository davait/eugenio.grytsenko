"""
User model module for the User Management Portal.

This module defines the User model using SQLAlchemy ORM,
including all necessary fields and their constraints.
"""

import logging
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from ..database import Base
from ..utils import validate_user_data, validate_email, validate_username, validate_department, VALID_DEPARTMENTS

# Configure logging
logger = logging.getLogger(__name__)

class User(Base):
    """
    User model representing a user in the system.
    
    Attributes:
        id (int): Primary key, auto-incrementing user ID
        email (str): Unique email address of the user
        username (str): Unique username for login
        hashed_password (str): Hashed password for security
        full_name (str): User's full name
        department (str): User's department (Tech, RRHH, or Sales)
        created_at (datetime): Timestamp of user creation
        updated_at (datetime): Timestamp of last update
    """
    
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    department = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __init__(self, **kwargs):
        """
        Initialize a new User instance.
        
        Args:
            **kwargs: Keyword arguments for user attributes
        """
        try:
            # Validate email and username before initialization
            if 'email' in kwargs and not validate_email(kwargs['email']):
                raise ValueError("Invalid email format")
            
            if 'username' in kwargs and not validate_username(kwargs['username']):
                raise ValueError("Invalid username format")
            
            # Validate department if provided
            if 'department' in kwargs and not validate_department(kwargs['department']):
                raise ValueError(f"Department must be one of: {', '.join(VALID_DEPARTMENTS)}")
            
            super().__init__(**kwargs)
            logger.info(f"New user instance created: {self.username}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating user instance: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise

    def __repr__(self):
        """
        String representation of the User instance.
        
        Returns:
            str: String representation of the user
        """
        return f"<User {self.username} - {self.department}>"

    @classmethod
    @validate_user_data
    def create(cls, db, **kwargs):
        """
        Create a new user in the database.
        
        Args:
            db: Database session
            **kwargs: User attributes
            
        Returns:
            User: Created user instance
            
        Raises:
            SQLAlchemyError: If database operation fails
            ValueError: If validation fails
        """
        try:
            user = cls(**kwargs)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"User created successfully: {user.username}")
            return user
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise
        except ValueError as e:
            db.rollback()
            logger.error(f"Validation error during user creation: {str(e)}")
            raise

    def update(self, db, **kwargs):
        """
        Update user attributes.
        
        Args:
            db: Database session
            **kwargs: User attributes to update
            
        Returns:
            User: Updated user instance
            
        Raises:
            SQLAlchemyError: If database operation fails
            ValueError: If validation fails
        """
        try:
            # Validate email and username if they are being updated
            if 'email' in kwargs and not validate_email(kwargs['email']):
                raise ValueError("Invalid email format")
            
            if 'username' in kwargs and not validate_username(kwargs['username']):
                raise ValueError("Invalid username format")
            
            # Validate department if it's being updated
            if 'department' in kwargs and not validate_department(kwargs['department']):
                raise ValueError(f"Department must be one of: {', '.join(VALID_DEPARTMENTS)}")
            
            for key, value in kwargs.items():
                setattr(self, key, value)
            
            db.commit()
            db.refresh(self)
            logger.info(f"User updated successfully: {self.username}")
            return self
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating user: {str(e)}")
            raise
        except ValueError as e:
            db.rollback()
            logger.error(f"Validation error during user update: {str(e)}")
            raise 