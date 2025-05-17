#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DynamoDB Service
---------------
This module handles all DynamoDB operations for the resume parser.
"""

import logging
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class DynamoDBService:
    """Service class for DynamoDB operations."""
    
    def __init__(self, table_name: str = "resume_processing"):
        """
        Initialize DynamoDB service.
        
        Args:
            table_name (str): Name of the DynamoDB table
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        
    def create_processing_record(
        self,
        filename: str,
        status: str = "in_progress"
    ) -> str:
        """
        Create a new processing record in DynamoDB.
        
        Args:
            filename (str): Original filename
            status (str): Initial status of the processing
            
        Returns:
            str: The generated processing ID
            
        Raises:
            ClientError: If there's an error with DynamoDB
        """
        try:
            processing_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            item = {
                'processing_id': processing_id,
                'filename': filename,
                'status': status,
                'created_at': timestamp,
                'updated_at': timestamp
            }
            
            self.table.put_item(Item=item)
            logger.info(f"Created processing record with ID: {processing_id}")
            return processing_id
            
        except ClientError as e:
            logger.error(f"Error creating processing record: {str(e)}")
            raise
            
    def update_processing_status(
        self,
        processing_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update the status of a processing record.
        
        Args:
            processing_id (str): The ID of the processing record
            status (str): New status
            result (Optional[Dict[str, Any]]): Processing result if available
            
        Raises:
            ClientError: If there's an error with DynamoDB
        """
        try:
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
                
            self.table.update_item(
                Key={'processing_id': processing_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names
            )
            
            logger.info(f"Updated processing record {processing_id} to status: {status}")
            
        except ClientError as e:
            logger.error(f"Error updating processing record: {str(e)}")
            raise
            
    def get_processing_record(self, processing_id: str) -> Dict[str, Any]:
        """
        Get a processing record by ID.
        
        Args:
            processing_id (str): The ID of the processing record
            
        Returns:
            Dict[str, Any]: The processing record
            
        Raises:
            ClientError: If there's an error with DynamoDB
        """
        try:
            response = self.table.get_item(
                Key={'processing_id': processing_id}
            )
            return response.get('Item', {})
            
        except ClientError as e:
            logger.error(f"Error getting processing record: {str(e)}")
            raise 