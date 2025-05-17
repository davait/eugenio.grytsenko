#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Lambda Function Locally
---------------------------
Script to test the Lambda function locally with DynamoDB local.
"""

import json
import logging
import os
from lambda_function import lambda_handler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_event():
    """Create a test event for the Lambda function."""
    return {
        "Records": [
            {
                "eventName": "INSERT",
                "dynamodb": {
                    "NewImage": {
                        "processing_id": {"S": "test-123"},
                        "status": {"S": "ai_ready_to_process"},
                        "s3_key": {"S": "uploads/incoming/test-123.pdf"}
                    }
                }
            }
        ]
    }

def test_lambda():
    """Test the Lambda function with a sample event."""
    try:
        # Set environment variables
        os.environ['DYNAMODB_TABLE'] = 'resume_processing'
        os.environ['S3_BUCKET'] = 'uploads'
        os.environ['GOOGLE_API_KEY'] = 'your-api-key'  # Replace with your API key
        
        # Create test event
        event = create_test_event()
        
        # Call Lambda handler
        logger.info("Testing Lambda function...")
        response = lambda_handler(event, None)
        
        # Log response
        logger.info(f"Lambda response: {json.dumps(response, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error testing Lambda: {str(e)}")
        raise

if __name__ == "__main__":
    test_lambda() 