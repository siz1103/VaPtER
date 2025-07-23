# plugins/gce_scanner/Dockerfile

FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first
RUN useradd -m -u 1000 scanner

# Set working directory
WORKDIR /app

# Copy requirements as root
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership
RUN chown -R scanner:scanner /app

# Create pip cache directory for scanner user
RUN mkdir -p /home/scanner/.cache/pip && \
    chown -R scanner:scanner /home/scanner/.cache

# Switch to non-root user
USER scanner

# Run the scanner
CMD ["python", "gce_scanner.py"]