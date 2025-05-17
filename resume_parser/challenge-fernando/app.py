#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resume Parser API
----------------
A FastAPI-based REST API for parsing resumes from PDF, PNG, and JPG files.
The API validates file types, performs OCR, and extracts structured information.

Author: Eugenio Grytsenko
Date: 2025
"""

import logging
import asyncio
from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import magic
import os
from typing import List, Dict, Any
from datetime import datetime
from services import process_resume_with_gemini
from dynamo_service import DynamoDBService
from s3_service import S3Service
import uuid

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Resume Parser API",
    description="API for parsing and extracting information from resume files",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
dynamo_service = DynamoDBService()
s3_service = S3Service()

# Allowed file types and their corresponding extensions
ALLOWED_MIME_TYPES: Dict[str, str] = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png"
}

async def process_resume_background(
    processing_id: str,
    s3_key: str,
    mime_type: str
) -> None:
    """
    Process a resume in the background.
    
    Args:
        processing_id (str): Processing record ID
        s3_key (str): S3 key of the file
        mime_type (str): MIME type of the file
    """
    try:
        # Get file from S3
        response = s3_service.s3.get_object(
            Bucket=s3_service.bucket_name,
            Key=s3_key
        )
        file_content = response['Body'].read()
        
        # Process the resume
        result = process_resume_with_gemini(
            file_content=file_content,
            mime_type=mime_type,
            api_key=os.getenv('GOOGLE_API_KEY')
        )
        
        # Update DynamoDB with success
        dynamo_service.update_processing_status(
            processing_id=processing_id,
            status="ai_finished",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        # Update DynamoDB with error
        dynamo_service.update_processing_status(
            processing_id=processing_id,
            status="error",
            result={"error": str(e)}
        )

@app.post("/api/resume/upload", 
         response_model=Dict[str, str],
         status_code=202,
         summary="Upload a resume file",
         description="Upload a resume file (PDF, PNG, or JPG) for processing")
async def upload_resume(
    file: UploadFile,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Upload a resume file for processing.
    
    Args:
        file (UploadFile): The uploaded file
        background_tasks (BackgroundTasks): FastAPI background tasks
        
    Returns:
        Dict[str, str]: Dictionary containing the processing ID
        
    Raises:
        HTTPException: If file is invalid or there's an error
    """
    logger.info(f"Received file upload request: {file.filename}")
    
    # Validate file presence
    if not file:
        logger.error("No file provided in request")
        raise HTTPException(
            status_code=400, 
            detail="No file provided"
        )
    
    try:
        # Validate file type
        mime_type = file.content_type
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
            )
            
        # Read file content
        file_content = await file.read()
        
        # Generate processing ID
        processing_id = str(uuid.uuid4())
        
        # Upload to S3
        s3_key = s3_service.upload_file(
            file_content=file_content,
            filename=file.filename,
            processing_id=processing_id
        )
        
        # Create initial record in DynamoDB
        dynamo_service.create_processing_record(
            processing_id=processing_id,
            s3_key=s3_key,
            mime_type=mime_type
        )
        
        # Start background processing
        background_tasks.add_task(
            process_resume_background,
            processing_id=processing_id,
            s3_key=s3_key,
            mime_type=mime_type
        )
        
        return {
            "processing_id": processing_id,
            "status": "in_progress",
            "message": "Resume upload successful, processing started"
        }
        
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading resume: {str(e)}"
        )

@app.get("/api/resume/status/{processing_id}",
         response_model=Dict[str, Any],
         summary="Get processing status",
         description="Get the status of a resume processing job")
async def get_processing_status(processing_id: str) -> Dict[str, Any]:
    """
    Get the status of a resume processing job.
    
    Args:
        processing_id (str): The ID of the processing record
        
    Returns:
        Dict[str, Any]: The processing record
        
    Raises:
        HTTPException: If the processing record is not found
    """
    try:
        record = dynamo_service.get_processing_record(processing_id)
        if not record:
            raise HTTPException(
                status_code=404,
                detail="Processing record not found"
            )
        return record
        
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting processing status: {str(e)}"
        ) 