"""
Resume Parser Lambda Function

This module implements an AWS Lambda function that processes uploaded resume files,
extracts text using OCR (for images) or PDF parsing, and uses Google's Gemini AI
to extract structured information from the resume content.
"""

import os
import json
import logging
import boto3
import requests
from typing import Dict, Any, List
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image
import PyPDF2
import io
import base64
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Configuration
aws_config = Config(
    region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
)

dynamodb_config = Config(
    region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
)

# Initialize AWS clients
s3 = boto3.client(
    's3',
    config=aws_config,
    endpoint_url=os.getenv('S3_ENDPOINT', 'http://localstack:4566'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'local'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'local')
)

dynamodb = boto3.resource(
    'dynamodb',
    config=dynamodb_config,
    endpoint_url=os.getenv('DYNAMODB_ENDPOINT', 'http://localstack:4566'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'local'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'local')
)
table = dynamodb.Table('Resumes')

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_content (bytes): Raw PDF file content
        
    Returns:
        str: Extracted text from the PDF
        
    Raises:
        PyPDF2.PdfReadError: If PDF is corrupted or cannot be read
    """
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        logger.info("Successfully extracted text from PDF")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise

def extract_text_from_image(image_content: bytes) -> str:
    """
    Extract text content from an image file using OCR.
    Currently returns placeholder text, but can be extended with Tesseract OCR.
    
    Args:
        image_content (bytes): Raw image file content
        
    Returns:
        str: Extracted text from the image
    """
    try:
        image = Image.open(io.BytesIO(image_content))
        # TODO: Implement OCR using Tesseract or similar
        logger.info("Image loaded successfully, OCR to be implemented")
        return "Sample resume text"
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise

def process_resume(file_content: bytes, file_type: str) -> Dict[str, Any]:
    """
    Process resume content using Gemini AI to extract structured information.
    
    Args:
        file_content (bytes): Raw file content
        file_type (str): MIME type of the file
        
    Returns:
        Dict[str, Any]: Structured resume information
        
    Raises:
        Exception: If processing fails
    """
    try:
        logger.info("Starting resume processing...")
        
        # Extract text based on file type
        if file_type == 'application/pdf':
            logger.info("Extracting text from PDF...")
            text = extract_text_from_pdf(file_content)
            logger.info(f"Extracted text length: {len(text)} characters")
        else:
            logger.info("Extracting text from image...")
            text = extract_text_from_image(file_content)
            logger.info(f"Extracted text length: {len(text)} characters")
        
        # Prepare prompt for Gemini
        prompt = f"""
        Analyze the following resume text and extract information in a specific JSON format.
        The response must be a valid JSON object with exactly these fields:
        {{
            "name": "full name of the candidate",
            "email": "email address",
            "skills": "comma-separated list of technical skills",
            "experience": [
                "detailed description of each work experience"
            ]
        }}

        Important:
        - All fields are required
        - skills should be a comma-separated string
        - experience should be an array of strings
        - Respond ONLY with the JSON, no additional text
        - Ensure the response is valid JSON

        Resume text:
        {text}
        """
        
        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
            
        logger.info("Configuring Gemini...")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro-vision')
        
        # Prepare content for Gemini
        contents = [prompt]
        
        # Add file content
        file_data = base64.b64encode(file_content).decode('utf-8')
        contents.append({
            "mime_type": file_type,
            "data": file_data
        })
        
        logger.info("Calling Gemini API...")
        response = model.generate_content(contents)
        
        # Extract the response text
        result_text = response.text
        logger.info(f"Received response from Gemini: {result_text[:100]}...")
        
        result = json.loads(result_text)
        
        # Validate required fields
        required_fields = ['name', 'email', 'skills', 'experience']
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
        
        logger.info("Successfully processed resume with Gemini")
        return result
        
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function that processes resume files.
    
    Args:
        event (Dict[str, Any]): Lambda event containing DynamoDB stream records
        context (Any): Lambda context object
        
    Returns:
        Dict[str, Any]: Response containing processing status
        
    Raises:
        Exception: If processing fails
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Process each record in the event
        for record in event['Records']:
            logger.info(f"Processing record: {json.dumps(record)}")
            
            if record['eventName'] == 'MODIFY':
                new_image = record['dynamodb']['NewImage']
                old_image = record['dynamodb']['OldImage']
                
                logger.info(f"New image: {json.dumps(new_image)}")
                logger.info(f"Old image: {json.dumps(old_image)}")
                
                # Only process if status changed to upload_finished
                if (new_image['status']['S'] == 'upload_finished' and 
                    old_image['status']['S'] != 'upload_finished'):
                    
                    file_id = new_image['id']['S']
                    logger.info(f"Processing file: {file_id}")
                    
                    try:
                        # Update status to processing
                        table.update_item(
                            Key={'id': file_id},
                            UpdateExpression='SET #status = :status',
                            ExpressionAttributeNames={'#status': 'status'},
                            ExpressionAttributeValues={':status': 'ai_thinking'}
                        )
                        logger.info(f"Updated status to ai_thinking for file: {file_id}")
                        
                        # Get file from S3
                        logger.info(f"Getting file from S3: {file_id}")
                        response = s3.get_object(
                            Bucket='resumes',
                            Key=file_id
                        )
                        file_content = response['Body'].read()
                        file_type = response['ContentType']
                        logger.info(f"Retrieved file from S3. Type: {file_type}, Size: {len(file_content)} bytes")
                        
                        # Process the file
                        result = process_resume(file_content, file_type)
                        
                        # Update DynamoDB with results
                        logger.info("Updating DynamoDB with results...")
                        table.update_item(
                            Key={'id': file_id},
                            UpdateExpression='SET #status = :status, ai_response = :response',
                            ExpressionAttributeNames={'#status': 'status'},
                            ExpressionAttributeValues={
                                ':status': 'completed',
                                ':response': result
                            }
                        )
                        logger.info(f"Successfully processed file: {file_id}")
                        
                        return {
                            'statusCode': 200,
                            'body': json.dumps({
                                'message': 'Processing completed',
                                'file_id': file_id
                            })
                        }
                        
                    except Exception as e:
                        error_message = f"Error processing file {file_id}: {str(e)}"
                        logger.error(error_message)
                        table.update_item(
                            Key={'id': file_id},
                            UpdateExpression='SET #status = :status, error_message = :error',
                            ExpressionAttributeNames={'#status': 'status'},
                            ExpressionAttributeValues={
                                ':status': 'error',
                                ':error': error_message
                            }
                        )
                        raise
                    
    except Exception as e:
        error_message = f"Lambda execution error: {str(e)}"
        logger.error(error_message)
        raise 