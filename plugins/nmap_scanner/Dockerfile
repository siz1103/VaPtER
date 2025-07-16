# plugins/nmap_scanner/Dockerfile

FROM kalilinux/kali-rolling

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Update and install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nmap \
    curl \
    netcat-traditional \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /tmp/nmap_results && \
    chmod 755 /tmp/nmap_results

# Create non-root user for security
RUN useradd -m -u 1000 nmap_user && \
    chown -R nmap_user:nmap_user /app /tmp/nmap_results

# Switch to non-root user
USER nmap_user

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import pika; pika.BlockingConnection(pika.URLParameters('${RABBITMQ_URL:-amqp://vapter:vapter123@rabbitmq:5672/}'))" || exit 1

# Run the scanner
CMD ["python3", "nmap_scanner.py"]