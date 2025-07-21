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
    curl \
    wget \
    git \
    golang-go \
    libcap2-bin \
    netcat-traditional \
    dnsutils \
    python3-requests \
    python3-dateutil \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python packages not available via apt
RUN pip3 install --break-system-packages pika==1.3.2 typing-extensions==4.8.0

# Install FingerprintX
RUN go install github.com/praetorian-inc/fingerprintx/cmd/fingerprintx@latest && \
    cp /root/go/bin/fingerprintx /usr/local/bin/ && \
    chmod +x /usr/local/bin/fingerprintx

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /tmp/fingerprint_results && \
    chmod 755 /tmp/fingerprint_results

# Create non-root user for security
RUN useradd -m -u 1000 fingerprint_user && \
    chown -R fingerprint_user:fingerprint_user /app /tmp/fingerprint_results

# Set capabilities for fingerprintx binary to allow raw socket operations
RUN setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip /usr/local/bin/fingerprintx || true

# Switch to non-root user
USER fingerprint_user

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import pika; pika.BlockingConnection(pika.URLParameters('${RABBITMQ_URL:-amqp://vapter:vapter123@rabbitmq:5672/}'))" || exit 1

# Run the scanner
CMD ["python3", "fingerprint_scanner.py"]