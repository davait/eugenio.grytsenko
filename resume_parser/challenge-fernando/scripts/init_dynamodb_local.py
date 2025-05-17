#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialize DynamoDB Local Table
------------------------------
Script to create the resume processing table in DynamoDB local.
"""

import boto3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_table():
    """Create the resume processing table in DynamoDB local."""
    try:
        # Create DynamoDB client for local instance
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        
        # Create table
        table = dynamodb.create_table(
            TableName='resume_processing',
            KeySchema=[
                {
                    'AttributeName': 'processing_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'processing_id',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        # Wait for table creation
        table.meta.client.get_waiter('table_exists').wait(TableName='resume_processing')
        logger.info("Table 'resume_processing' created successfully")
        
    except Exception as e:
        logger.error(f"Error creating table: {str(e)}")
        raise

if __name__ == "__main__":
    create_table() 