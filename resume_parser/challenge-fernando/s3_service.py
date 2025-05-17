#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S3 Service
----------
This module handles all S3 operations for the resume parser.
"""

import logging
import boto3
from botocore.exceptions import ClientError
from typing import Optional
import os

logger = logging.getLogger(__name__)

class S3Service:
    """Service class for S3 operations."""
    
    def __init__(self, bucket_name: str = "uploads"):
        """
        Initialize S3 service.
        
        Args:
            bucket_name (str): Name of the S3 bucket
        """
        self.s3 = boto3.client('s3')
        self.bucket_name = bucket_name
        
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        processing_id: str
    ) -> str:
        """
        Upload a file to S3.
        
        Args:
            file_content (bytes): The content of the file
            filename (str): Original filename
            processing_id (str): The processing ID for the file
            
        Returns:
            str: The S3 key of the uploaded file
            
        Raises:
            ClientError: If there's an error with S3
        """
        try:
            # Generate S3 key
            file_extension = os.path.splitext(filename)[1]
            s3_key = f"incoming/{processing_id}{file_extension}"
            
            # Upload file
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=self._get_content_type(file_extension)
            )
            
            logger.info(f"Uploaded file to S3: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise
            
    def get_file_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for a file.
        
        Args:
            s3_key (str): The S3 key of the file
            expires_in (int): URL expiration time in seconds
            
        Returns:
            str: Presigned URL
            
        Raises:
            ClientError: If there's an error with S3
        """
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expires_in
            )
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise
            
    def _get_content_type(self, file_extension: str) -> str:
        """
        Get the content type for a file extension.
        
        Args:
            file_extension (str): The file extension
            
        Returns:
            str: The content type
        """
        content_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream') 