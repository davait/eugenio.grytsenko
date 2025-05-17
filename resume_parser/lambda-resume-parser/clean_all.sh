#!/bin/bash

echo "🧹 Cleaning up..."

# Stop and remove containers
echo "Stopping containers..."
docker-compose down
docker-compose down -v

# Remove volumes
echo "Removing volumes..."
docker volume rm lambda-resume-parser_localstack-data 2>/dev/null || true

# Clean lambda directory
echo "Cleaning lambda directory..."
cd lambda
# Save essential files
cp lambda_function.py ../lambda_function.py.bak
cp requirements.txt ../requirements.txt.bak
cp Dockerfile ../Dockerfile.bak
# Remove everything
rm -rf *
# Restore essential files
mv ../lambda_function.py.bak lambda_function.py
mv ../requirements.txt.bak requirements.txt
mv ../Dockerfile.bak Dockerfile
cd ..
rm -f lambda.zip
docker rm -f $(docker ps -a | grep "localstack-lambda-resume-parser" | awk '{print $1}') 2>/dev/null

echo "✅ Cleanup completed!" 
