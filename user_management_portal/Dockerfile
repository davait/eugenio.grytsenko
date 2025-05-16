# Build frontend
FROM node:18-alpine as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Build backend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend build from previous stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0
ENV FRONTEND_URL=https://your-cloud-run-url.run.app

# Expose the port
EXPOSE 8080

# Create a non-root user
RUN useradd -m myuser
USER myuser

# Command to run the application
CMD uvicorn backend.main:app --host $HOST --port $PORT
