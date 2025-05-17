#!/bin/bash

# Function to check if a command is available
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "Error: $1 is not installed. Please install it before continuing."
        exit 1
    fi
}

# Check required dependencies
check_command aws
check_command curl
check_command zip

# Function to check service status
check_service() {
    local service=$1
    local max_attempts=30
    local attempt=1
    
    echo "Checking $service status..."
    while [ $attempt -le $max_attempts ]; do
        local health_status=$(curl -s http://localhost:4566/_localstack/health)
        if echo "$health_status" | grep -q "\"$service\": \"running\"" || echo "$health_status" | grep -q "\"$service\": \"available\""; then
            echo "✅ $service is ready!"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts: Waiting for $service..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Error: $service is not available after $max_attempts attempts"
    echo "Current health status:"
    echo "$health_status"
    return 1
}

# Function to check if a resource exists
check_resource_exists() {
    local resource_type=$1
    local resource_name=$2
    
    case $resource_type in
        "lambda")
            aws --endpoint-url=http://localhost:4566 lambda get-function --function-name "$resource_name" &>/dev/null
            ;;
        "dynamodb")
            aws --endpoint-url=http://localhost:4566 dynamodb describe-table --table-name "$resource_name" &>/dev/null
            ;;
        "s3")
            aws --endpoint-url=http://localhost:4566 s3api head-bucket --bucket "$resource_name" &>/dev/null
            ;;
    esac
    return $?
}

# Function to execute AWS commands with error handling and sensitive data masking
run_aws_command() {
    local description=$1
    local resource_type=$2
    local resource_name=$3
    shift 3
    
    echo "📝 $description..."
    
    # Check if resource exists
    if check_resource_exists "$resource_type" "$resource_name"; then
        echo "ℹ️  $resource_type '$resource_name' already exists, skipping creation"
        return 0
    fi
    
    # Execute command and capture output
    local output
    if ! output=$(aws --endpoint-url=http://localhost:4566 "$@" 2>&1); then
        # Check for specific error types
        if echo "$output" | grep -q "ResourceConflictException"; then
            echo "ℹ️  Resource already exists, continuing..."
            return 0
        else
            echo "❌ Error executing: $description"
            echo "$output" | sed 's/"GEMINI_API_KEY": "[^"]*"/"GEMINI_API_KEY": "***"/g'
            exit 1
        fi
    fi
    
    # Print masked output
    echo "$output" | sed 's/"GEMINI_API_KEY": "[^"]*"/"GEMINI_API_KEY": "***"/g'
    echo "✅ $description completed"
}

# Check main services
check_service "dynamodb" || exit 1
check_service "lambda" || exit 1
check_service "s3" || exit 1

# Check DynamoDB Streams (non-blocking)
DDB_STREAMS_STATUS=$(curl -s http://localhost:4566/_localstack/health | grep '"dynamodbstreams"')
if [[ "$DDB_STREAMS_STATUS" == *'"available"'* ]]; then
    echo "✅ DynamoDB Streams is available"
else
    echo "⚠️  Warning: DynamoDB Streams is not 'available'. Continuing anyway..."
fi

# Create AWS resources
run_aws_command "Creating S3 bucket" "s3" "resumes" s3 mb s3://resumes

run_aws_command "Creating DynamoDB table" "dynamodb" "Resumes" dynamodb create-table \
    --table-name Resumes \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --stream-specification \
        StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES

# Create Lambda deployment package
echo "📦 Creating Lambda deployment package..."
if [ ! -d "lambda" ]; then
    echo "❌ Error: 'lambda' directory does not exist"
    exit 1
fi

cd lambda
if ! zip -q -r ../lambda.zip .; then
    echo "❌ Error creating ZIP file"
    exit 1
fi
cd ..

# Check GEMINI_API_KEY
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: GEMINI_API_KEY environment variable is not set"
    echo "Please set it using: export GEMINI_API_KEY=your_api_key"
    exit 1
fi

# Create Lambda function
echo "📝 Creating Lambda function..."
aws --endpoint-url=http://localhost:4566 lambda create-function \
    --function-name resume-parser \
    --runtime python3.9 \
    --handler lambda_function.lambda_handler \
    --role arn:aws:iam::000000000000:role/lambda-role \
    --zip-file fileb://lambda.zip \
    --timeout 300 \
    --memory-size 512 \
    --environment "Variables={GEMINI_API_KEY=$GEMINI_API_KEY}"

# Get stream ARN and create event source mapping
echo "🔍 Getting DynamoDB stream ARN..."
STREAM_ARN=$(aws --endpoint-url=http://localhost:4566 dynamodb describe-table --table-name Resumes --query 'Table.LatestStreamArn' --output text)

if [ -z "$STREAM_ARN" ]; then
    echo "❌ Error: Could not get stream ARN"
    exit 1
fi

echo "📝 Stream ARN: $STREAM_ARN"

# Delete existing event source mapping if it exists
echo "🧹 Cleaning up existing event source mappings..."
aws --endpoint-url=http://localhost:4566 lambda list-event-source-mappings --function-name resume-parser | \
    grep -o '"UUID": "[^"]*"' | \
    cut -d'"' -f4 | \
    while read uuid; do
        echo "Deleting mapping: $uuid"
        aws --endpoint-url=http://localhost:4566 lambda delete-event-source-mapping --uuid "$uuid"
    done

# Wait for any deletions to complete
sleep 5

# Create new event source mapping
echo "🔗 Creating new event source mapping..."
aws --endpoint-url=http://localhost:4566 lambda create-event-source-mapping \
    --function-name resume-parser \
    --event-source-arn "$STREAM_ARN" \
    --batch-size 1 \
    --starting-position LATEST \
    --enabled

# Wait for mapping to be created
sleep 5

# Verify event source mapping
echo "🔍 Verifying event source mapping..."
aws --endpoint-url=http://localhost:4566 lambda list-event-source-mappings --function-name resume-parser

echo "🎉 Initialization completed successfully!" 
