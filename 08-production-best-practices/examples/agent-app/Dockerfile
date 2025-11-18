# Dockerfile for Production Agent System

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 agentuser && \
    chown -R agentuser:agentuser /app

USER agentuser

# Expose ports
EXPOSE 8001 9091

# Default command (can be overridden)
CMD ["celery", "-A", "agent", "worker", "--loglevel=info", "--concurrency=4"]
