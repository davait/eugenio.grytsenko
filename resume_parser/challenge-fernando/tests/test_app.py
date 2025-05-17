#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Resume Parser API
-------------------------------
Tests for the FastAPI endpoints and services using pytest and mocks.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import json
import os
from app import app
from services import process_resume_with_gemini
from dynamo_service import DynamoDBService
from s3_service import S3Service

# Create test client
client = TestClient(app)

# Mock data
MOCK_PROCESSING_ID = "test-123"
MOCK_S3_KEY = "uploads/incoming/test-123.pdf"
MOCK_MIME_TYPE = "application/pdf"
MOCK_RESULT = {
    "personal_info": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "location": "New York"
    },
    "summary": "Experienced software engineer",
    "experience": [
        {
            "title": "Senior Developer",
            "company": "Tech Corp",
            "period": "2020-2023",
            "description": "Led development team"
        }
    ],
    "education": [
        {
            "degree": "BS Computer Science",
            "institution": "University",
            "period": "2016-2020"
        }
    ],
    "skills": ["Python", "FastAPI", "AWS"],
    "languages": ["English", "Spanish"],
    "certifications": ["AWS Certified"]
}

@pytest.fixture
def mock_dynamo_service():
    """Mock DynamoDB service."""
    with patch('app.dynamo_service') as mock:
        mock.create_processing_record = Mock(return_value=MOCK_PROCESSING_ID)
        mock.update_processing_status = Mock()
        mock.get_processing_record = Mock(return_value={
            "processing_id": MOCK_PROCESSING_ID,
            "status": "ai_finished",
            "result": MOCK_RESULT
        })
        yield mock

@pytest.fixture
def mock_s3_service():
    """Mock S3 service."""
    with patch('app.s3_service') as mock:
        mock.upload_file = Mock(return_value=MOCK_S3_KEY)
        mock.s3.get_object = Mock(return_value={
            'Body': MagicMock(read=lambda: b'test file content')
        })
        yield mock

@pytest.fixture
def mock_gemini_service():
    """Mock Gemini service."""
    with patch('app.process_resume_with_gemini') as mock:
        mock.return_value = MOCK_RESULT
        yield mock

def test_upload_resume_success(mock_dynamo_service, mock_s3_service, mock_gemini_service):
    """Test successful resume upload."""
    # Create test file
    test_file = ("test.pdf", b"test file content", "application/pdf")
    
    # Make request
    response = client.post(
        "/api/resume/upload",
        files={"file": test_file}
    )
    
    # Assert response
    assert response.status_code == 202
    data = response.json()
    assert "processing_id" in data
    assert data["status"] == "in_progress"
    assert "message" in data
    
    # Verify service calls
    mock_s3_service.upload_file.assert_called_once()
    mock_dynamo_service.create_processing_record.assert_called_once()
    mock_dynamo_service.update_processing_status.assert_called_once_with(
        processing_id=data["processing_id"],
        status="ai_finished",
        result=MOCK_RESULT
    )

def test_upload_resume_invalid_type(mock_dynamo_service, mock_s3_service):
    """Test resume upload with invalid file type."""
    # Create test file with invalid type
    test_file = ("test.txt", b"test content", "text/plain")
    
    # Make request
    response = client.post(
        "/api/resume/upload",
        files={"file": test_file}
    )
    
    # Assert response
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
    
    # Verify no service calls
    mock_s3_service.upload_file.assert_not_called()
    mock_dynamo_service.create_processing_record.assert_not_called()

def test_upload_resume_no_file():
    """Test resume upload with no file."""
    # Make request without file
    response = client.post("/api/resume/upload")
    
    # Assert response
    assert response.status_code == 422  # FastAPI validation error

def test_get_processing_status_success(mock_dynamo_service):
    """Test successful status retrieval."""
    # Make request
    response = client.get(f"/api/resume/status/{MOCK_PROCESSING_ID}")
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["processing_id"] == MOCK_PROCESSING_ID
    assert data["status"] == "ai_finished"
    assert "result" in data
    
    # Verify service call
    mock_dynamo_service.get_processing_record.assert_called_once_with(MOCK_PROCESSING_ID)

def test_get_processing_status_not_found(mock_dynamo_service):
    """Test status retrieval for non-existent record."""
    # Configure mock to return None
    mock_dynamo_service.get_processing_record.return_value = None
    
    # Make request
    response = client.get(f"/api/resume/status/{MOCK_PROCESSING_ID}")
    
    # Assert response
    assert response.status_code == 404
    assert "Processing record not found" in response.json()["detail"]
    
    # Verify service call
    mock_dynamo_service.get_processing_record.assert_called_once_with(MOCK_PROCESSING_ID)

def test_process_resume_background_error(mock_dynamo_service, mock_s3_service, mock_gemini_service):
    """Test background processing error handling."""
    # Configure mock to raise exception
    mock_gemini_service.side_effect = Exception("Test error")
    
    # Create test file
    test_file = ("test.pdf", b"test file content", "application/pdf")
    
    # Make request
    response = client.post(
        "/api/resume/upload",
        files={"file": test_file}
    )
    
    # Assert response
    assert response.status_code == 202
    data = response.json()
    
    # Verify error status update
    mock_dynamo_service.update_processing_status.assert_called_with(
        processing_id=data["processing_id"],
        status="error",
        result={"error": "Test error"}
    ) 