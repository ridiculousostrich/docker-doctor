# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies  
RUN apt-get update && apt-get install -y \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add optional AI provider dependencies based on environment variable
ARG AI_PROVIDER=ollama
RUN if [ "$AI_PROVIDER" = "openai" ]; then \
        pip install --no-cache-dir openai; \
    elif [ "$AI_PROVIDER" = "anthropic" ]; then \
        pip install --no-cache-dir anthropic; \
    fi

# Copy application code
COPY src/ ./src/
COPY config.example.yaml .

# Copy the Flask API server code and requirements
COPY backend/api/ /app/backend/api/

RUN pip install --no-cache-dir -r /app/backend/api/requirements.txt

# Create data directory
RUN mkdir -p /app/data

# Set Python path
ENV PYTHONPATH=/app

# Copy frontend source for build step
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY frontend/tsconfig.json frontend/
COPY frontend/public ./frontend/public/
COPY frontend/src ./frontend/src/

# Build the React frontend for production
WORKDIR /app/frontend
RUN npm install --legacy-peer-deps && npm run build

# Copy built frontend assets and startup scripts to app root
WORKDIR /app
COPY docker-run.sh /app/docker-run.sh
RUN chmod +x /app/docker-run.sh

# Expose port for the API/server (Flask serves both API + static frontend)
EXPOSE 8586

# Default command - single CMD (removed duplicate)
CMD ["/app/docker-run.sh"]
