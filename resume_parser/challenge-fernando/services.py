#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resume Parser Services
---------------------
This module contains the core business logic for processing resumes using Gemini AI.
"""

import base64
import logging
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from fastapi import HTTPException
from PIL import Image
import io
import magic
from pdf2image import convert_from_bytes

# Configure logging
logger = logging.getLogger(__name__)

# Gemini prompt template
RESUME_ANALYSIS_PROMPT = """
As an expert in data extraction from PDF, PNG, or JPG documents, you will receive a resume and must analyze it to extract the following candidate information. Return the output in JSON format with the following fields. If you cannot find information for any field, assign `null`:

{
    "name": <STRING|null>,
    "email": <STRING|null>,
    "skills": [<STRING>,...|null],
    "experience": [<STRING>,...|null]
}
"""

class ResumeProcessingError(Exception):
    """Custom exception for resume processing errors."""
    pass

def get_file_type(file_content: bytes) -> str:
    """
    Detect the MIME type of the file content.
    
    Args:
        file_content (bytes): The raw content of the file
        
    Returns:
        str: The MIME type of the file
    """
    mime = magic.Magic(mime=True)
    return mime.from_buffer(file_content)

def process_pdf(file_content: bytes) -> List[Image.Image]:
    """
    Convert PDF bytes to a list of PIL Images.
    
    Args:
        file_content (bytes): The raw content of the PDF file
        
    Returns:
        List[Image.Image]: List of PIL Images, one per page
        
    Raises:
        ResumeProcessingError: If there's an error converting the PDF
    """
    try:
        logger.info("Converting PDF to images")
        images = convert_from_bytes(file_content)
        logger.info(f"Successfully converted PDF to {len(images)} images")
        return images
    except Exception as e:
        logger.error(f"Error converting PDF to images: {str(e)}")
        raise ResumeProcessingError(f"Error processing PDF: {str(e)}")

def process_image(file_content: bytes) -> Image.Image:
    """
    Convert image bytes to a PIL Image.
    
    Args:
        file_content (bytes): The raw content of the image file
        
    Returns:
        Image.Image: PIL Image object
        
    Raises:
        ResumeProcessingError: If there's an error processing the image
    """
    try:
        logger.info("Processing image file")
        image = Image.open(io.BytesIO(file_content))
        logger.info("Successfully processed image")
        return image
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise ResumeProcessingError(f"Error processing image: {str(e)}")

def process_resume_with_gemini(
    file_content: bytes,
    mime_type: str,
    api_key: str
) -> Dict[str, Any]:
    """
    Process a resume using Gemini AI.
    
    Args:
        file_content (bytes): The content of the resume file
        mime_type (str): The MIME type of the file
        api_key (str): Google API key for Gemini
        
    Returns:
        Dict[str, Any]: Structured resume data
        
    Raises:
        Exception: If there's an error processing the resume
    """
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro-vision')
        
        # Create image part
        image = Image.open(io.BytesIO(file_content))
        
        # Create multimodal prompt
        prompt = """
        Analyze this resume and extract the following information in JSON format:
        {
            "personal_info": {
                "name": "Full name",
                "email": "Email address",
                "phone": "Phone number",
                "location": "Location"
            },
            "summary": "Professional summary",
            "experience": [
                {
                    "title": "Job title",
                    "company": "Company name",
                    "period": "Time period",
                    "description": "Job responsibilities"
                }
            ],
            "education": [
                {
                    "degree": "Degree name",
                    "institution": "Institution name",
                    "period": "Time period"
                }
            ],
            "skills": ["List of skills"],
            "languages": ["List of languages"],
            "certifications": ["List of certifications"]
        }
        
        Rules:
        1. If any field is not present, leave it empty
        2. Keep valid JSON format
        3. Extract only information explicitly present in the resume
        4. Do not invent information
        5. If there is additional relevant information, include it in additional fields
        """
        
        # Generate content
        response = model.generate_content([prompt, image])
        
        # Parse response
        try:
            result = response.json()
            logger.info("Successfully processed resume with Gemini")
            return result
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Error processing resume with Gemini: {str(e)}")
        raise 