# Resume Parser API

This project implements a resume parsing API using AWS Lambda, API Gateway, DynamoDB, and S3, all running locally with Docker Compose.

## Features

- File upload support for PDF, PNG, and JPG formats
- Automatic text extraction from PDFs
- Image OCR support (to be implemented)
- AI-powered resume analysis using Google's Gemini
- Structured JSON output with candidate information
- Real-time processing status tracking
- Local AWS service simulation

## Requirements

- Docker and Docker Compose
- Python 3.9+
- Google Gemini API Key

## Configuration

1. Clone the repository
2. Create a `.env` file in the project root with the following variables:
```
GEMINI_API_KEY=your_api_key_here
```

## Project Structure

```
.
├── api-gateway/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── lambda/
│   ├── Dockerfile
│   ├── lambda_function.py
│   └── requirements.txt
├── docker-compose.yml
└── README.md
```

## API Endpoints

### POST /upload
Upload a resume file for processing.

**Request:**
```bash
curl -X POST -F "file=@your_resume.pdf" http://localhost:3000/upload
```

**Response:**
```json
{
    "id": "file-uuid",
    "status": "upload_finished",
    "message": "File uploaded successfully"
}
```

### GET /status/{file_id}
Get the processing status and results for a file.

**Response:**
```json
{
    "id": "file-uuid",
    "status": "completed",
    "created_at": "2024-01-01T00:00:00",
    "mime_type": "application/pdf",
    "ai_response": {
        "name": "Candidate Name",
        "email": "email@example.com",
        "skills": ["skill1", "skill2"],
        "experience": ["exp1", "exp2"]
    }
}
```

## Processing States

1. `upload_in_progress`: File is being uploaded
2. `upload_finished`: File upload completed successfully
3. `ai_thinking`: AI model is processing the file
4. `completed`: Processing completed successfully
5. `error`: An error occurred during processing

## Local Development

1. Start the services:
```bash
docker-compose up --build
```

2. Services will be available at:
- API Gateway: http://localhost:3000
- DynamoDB Local: http://localhost:8000
- LocalStack (S3): http://localhost:4566

## Implementation Details

### API Gateway
- Built with FastAPI
- Handles file uploads and status checks
- Integrates with S3 and DynamoDB
- Implements proper error handling and logging

### Lambda Function
- Processes uploaded files
- Extracts text from PDFs and images
- Uses Gemini AI for resume analysis
- Updates processing status in DynamoDB

### AWS Services (Local)
- S3 simulated using LocalStack
- DynamoDB running locally
- Lambda function containerized

## Error Handling

The system implements comprehensive error handling:
- File validation
- AWS service errors
- Processing errors
- AI model errors

All errors are logged and appropriate status updates are made in DynamoDB.

## Logging

Both the API Gateway and Lambda function implement detailed logging:
- Request/response logging
- Error logging
- Processing status updates
- AWS service interactions

## Future Improvements

1. Implement OCR for image processing
2. Add support for more file formats
3. Implement retry mechanisms for failed processing
4. Add authentication and authorization
5. Implement rate limiting
6. Add unit and integration tests

## Local Execution Instructions

### Prerequisites
- Docker and Docker Compose installed
- Node.js (v14 or higher)
- Python 3.9
- Gemini API key (Google AI)

### Steps to Run

1. **Configure Environment Variables**
   ```bash
   # Create .env file in the project root
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

2. **Start Services**
   ```bash
   # Build and start all services
   docker-compose up --build
   ```

3. **Verify Services are Running**
   - API Gateway: http://localhost:3000
   - LocalStack: http://localhost:4566
   - DynamoDB Local: http://localhost:8000

4. **Test the System**
   ```bash
   # Example curl to test the processing endpoint
   curl -X POST http://localhost:3000/process \
     -H "Content-Type: application/json" \
     -d '{"resumeUrl": "https://example.com/resume.pdf"}'
   ```

### Troubleshooting

If you encounter issues starting the services:

1. **Clean Containers and Volumes**
   ```bash
   docker-compose down -v
   ```

2. **Check Logs**
   ```bash
   # View logs for all services
   docker-compose logs -f
   
   # View logs for a specific service
   docker-compose logs -f localstack
   ```

3. **Restart Services**
   ```bash
   docker-compose restart
   ```

### Important Notes
- Ensure port 3000 is available for the API Gateway
- The Lambda service may take a few minutes to fully initialize
- LocalStack logs are useful for debugging Lambda function issues
