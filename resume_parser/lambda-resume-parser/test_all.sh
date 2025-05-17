#!/bin/bash

echo "🚀 Starting complete system test..."

# Check if API Gateway is running
if ! curl -s http://localhost:3000/health &>/dev/null; then
    echo "📦 Building and starting API Gateway..."
    cd api-gateway
    docker build -t resume-api . || { echo "❌ Error building API Gateway"; exit 1; }
    docker run -d -p 3000:3000 --name resume-api resume-api || { echo "❌ Error starting API Gateway"; exit 1; }
    cd ..
    echo "✅ API Gateway started"
else
    echo "✅ API Gateway is already running"
fi

# Wait for API Gateway to be ready
echo "⏳ Waiting for API Gateway to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:3000/health &>/dev/null; then
        echo "✅ API Gateway is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ API Gateway failed to start"
        exit 1
    fi
    echo "Attempt $i/30..."
    sleep 2
done

# Run basic upload test
echo -e "\n📝 Running basic upload test..."
python test_upload.py || { echo "❌ Basic upload test failed"; exit 1; }

# Run comprehensive endpoint tests
echo -e "\n📝 Running comprehensive endpoint tests..."
python test_endpoints.py || { echo "❌ Endpoint tests failed"; exit 1; }

echo -e "\n🎉 All tests completed successfully!" 