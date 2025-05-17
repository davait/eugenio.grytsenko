#!/bin/bash

echo "Creating Lambda deployment package..."

# Install dependencies
cd lambda
pip install -r requirements.txt -t .

# Create ZIP file
zip -q -r ../lambda.zip .

# Clean up
rm -rf google* PIL* PyPDF2* boto3* botocore* jmespath* python_dateutil* s3transfer* six* urllib3* requests*

cd ..

echo "Lambda deployment package created: lambda.zip" 
