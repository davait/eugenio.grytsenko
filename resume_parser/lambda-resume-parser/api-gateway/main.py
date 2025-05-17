"""
Resume Parser API Gateway

This module implements a FastAPI-based API Gateway that handles resume file uploads,
integrates with AWS S3 for storage, and DynamoDB for state management.
"""

import os
import uuid
import logging
import boto3
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, UploadFile, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from botocore.config import Config
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume Parser API",
    description="API for uploading and processing resume files",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def create_dynamodb_table() -> None:
    """
    Creates the DynamoDB table if it doesn't exist.
    
    Raises:
        ClientError: If there's an error creating the table
    """
    try:
        table = dynamodb.create_table(
            TableName='Resumes',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            StreamSpecification={
                'StreamEnabled': True,
                'StreamViewType': 'NEW_AND_OLD_IMAGES'
            },
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        logger.info("DynamoDB table created successfully")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            logger.info("Table already exists")
        else:
            logger.error(f"Error creating table: {str(e)}")
            raise

# Create DynamoDB table on startup
create_dynamodb_table()
table = dynamodb.Table('Resumes')

# Create S3 bucket if it doesn't exist
try:
    s3.create_bucket(
        Bucket='resumes'
    )
    logger.info("S3 bucket created successfully")
except ClientError as e:
    if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
        logger.info("Bucket already exists")
    else:
        logger.error(f"Error creating bucket: {str(e)}")
        raise

@app.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile) -> Dict[str, Any]:
    """
    Upload a resume file and initiate processing.
    
    Args:
        file (UploadFile): The resume file to upload (PDF, PNG, or JPG)
        
    Returns:
        Dict[str, Any]: Response containing file ID and status
        
    Raises:
        HTTPException: If file is invalid or upload fails
    """
    logger.info(f"Received file upload request: {file.filename}")
    
    if not file.filename:
        logger.error("No file provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    file_id = str(uuid.uuid4())
    file_extension = file.filename.split('.')[-1].lower()
    
    if file_extension not in ['pdf', 'png', 'jpg', 'jpeg']:
        logger.error(f"Invalid file type: {file_extension}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Supported formats: PDF, PNG, JPG"
        )
    
    try:
        # Create DynamoDB record
        table.put_item(
            Item={
                'id': file_id,
                'status': 'upload_in_progress',
                'created_at': datetime.utcnow().isoformat(),
                'mime_type': file.content_type
            }
        )
        logger.info(f"Created DynamoDB record for file: {file_id}")
        
        # Upload to S3
        s3.upload_fileobj(
            file.file,
            'resumes',
            f"{file_id}.{file_extension}"
        )
        logger.info(f"Uploaded file to S3: {file_id}")
        
        # Update status
        table.update_item(
            Key={'id': file_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'upload_finished'}
        )
        logger.info(f"Updated status to upload_finished for file: {file_id}")
        
        return {
            "id": file_id,
            "status": "upload_finished",
            "message": "File uploaded successfully"
        }
        
    except ClientError as e:
        logger.error(f"AWS error: {str(e)}")
        table.update_item(
            Key={'id': file_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'error'}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AWS error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@app.get("/status/{file_id}")
async def get_status(file_id: str) -> Dict[str, Any]:
    """
    Get the processing status of a resume file.
    
    Args:
        file_id (str): The UUID of the uploaded file
        
    Returns:
        Dict[str, Any]: The current status and processing results
        
    Raises:
        HTTPException: If file is not found or status check fails
    """
    logger.info(f"Checking status for file: {file_id}")
    
    try:
        response = table.get_item(Key={'id': file_id})
        if 'Item' not in response:
            logger.error(f"File not found: {file_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        logger.info(f"Retrieved status for file: {file_id}")
        return response['Item']
        
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DynamoDB error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@app.get("/resumes", response_model=List[Dict[str, Any]])
async def list_resumes(
    limit: int = Query(default=10, ge=1, le=100),
    status: str = Query(default=None, description="Filter by status")
) -> List[Dict[str, Any]]:
    """
    List all resumes in the database with optional filtering.
    
    Args:
        limit (int): Maximum number of items to return (1-100)
        status (str, optional): Filter by status
        
    Returns:
        List[Dict[str, Any]]: List of resume records
        
    Raises:
        HTTPException: If there's an error retrieving the records
    """
    logger.info(f"Listing resumes with limit={limit}, status={status}")
    
    try:
        # Build scan parameters
        scan_params = {
            'Limit': limit
        }
        
        # Add status filter if provided
        if status:
            scan_params['FilterExpression'] = '#status = :status'
            scan_params['ExpressionAttributeNames'] = {'#status': 'status'}
            scan_params['ExpressionAttributeValues'] = {':status': status}
        
        # Perform scan
        response = table.scan(**scan_params)
        items = response.get('Items', [])
        
        # Handle pagination if there are more items
        while 'LastEvaluatedKey' in response and len(items) < limit:
            scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = table.scan(**scan_params)
            items.extend(response.get('Items', []))
            
            if len(items) >= limit:
                items = items[:limit]
                break
        
        logger.info(f"Retrieved {len(items)} resumes")
        return items
        
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DynamoDB error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        ) 