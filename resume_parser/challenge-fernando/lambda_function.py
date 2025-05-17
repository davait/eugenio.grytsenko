#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resume Parser Lambda Function
----------------------------
This Lambda function is triggered by DynamoDB Streams when a new record
with status 'ai_ready_to_process' is inserted. It processes the resume
file using Gemini AI.
"""

import json
import os
import logging
import boto3
from botocore.exceptions import ClientError
from services import process_resume_with_gemini
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

def get_file_from_s3(bucket: str, key: str) -> bytes:
    """
    Get file content from S3.
    
    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        
    Returns:
        bytes: File content
        
    Raises:
        ClientError: If there's an error accessing S3
    """
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
    except ClientError as e:
        logger.error(f"Error getting file from S3: {str(e)}")
        raise

def update_dynamodb_status(
    table_name: str,
    processing_id: str,
    status: str,
    result: dict = None
) -> None:
    """
    Update the status of a processing record in DynamoDB.
    
    Args:
        table_name (str): DynamoDB table name
        processing_id (str): Processing record ID
        status (str): New status
        result (dict): Optional result data
        
    Raises:
        ClientError: If there's an error updating DynamoDB
    """
    try:
        table = dynamodb.Table(table_name)
        update_expression = "SET #status = :status, updated_at = :updated_at"
        expression_values = {
            ':status': status,
            ':updated_at': datetime.utcnow().isoformat()
        }
        expression_names = {
            '#status': 'status'
        }
        
        if result is not None:
            update_expression += ", result = :result"
            expression_values[':result'] = result
            
        table.update_item(
            Key={'processing_id': processing_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names
        )
        
        logger.info(f"Updated processing record {processing_id} to status: {status}")
        
    except ClientError as e:
        logger.error(f"Error updating DynamoDB: {str(e)}")
        raise

def lambda_handler(event: dict, context: dict) -> dict:
    """
    Lambda function handler.
    
    Args:
        event (dict): Lambda event data
        context (dict): Lambda context
        
    Returns:
        dict: Response data
    """
    try:
        # Get environment variables
        table_name = os.environ['DYNAMODB_TABLE']
        bucket_name = os.environ['S3_BUCKET']
        api_key = os.environ['GOOGLE_API_KEY']
        
        # Process each record in the event
        for record in event['Records']:
            # Check if this is an INSERT event
            if record['eventName'] != 'INSERT':
                continue
                
            # Get the new image data
            new_image = record['dynamodb']['NewImage']
            
            # Check if status is 'ai_ready_to_process'
            if new_image['status']['S'] != 'ai_ready_to_process':
                continue
                
            # Get processing ID and S3 key
            processing_id = new_image['processing_id']['S']
            s3_key = new_image['s3_key']['S']
            
            logger.info(f"Processing resume {processing_id} from S3 key: {s3_key}")
            
            try:
                # Get file from S3
                file_content = get_file_from_s3(bucket_name, s3_key)
                
                # Process the resume
                result = process_resume_with_gemini(file_content, api_key)
                
                # Update DynamoDB with success and status 'ai_finished'
                update_dynamodb_status(
                    table_name=table_name,
                    processing_id=processing_id,
                    status="ai_finished",
                    result=result
                )
                
            except Exception as e:
                logger.error(f"Error processing resume {processing_id}: {str(e)}")
                # Update DynamoDB with error
                update_dynamodb_status(
                    table_name=table_name,
                    processing_id=processing_id,
                    status="error",
                    result={"error": str(e)}
                )
                
        return {
            'statusCode': 200,
            'body': json.dumps('Processing completed')
        }
        
    except Exception as e:
        logger.error(f"Error in Lambda function: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        } 