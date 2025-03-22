FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies including Chrome and required libraries
# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libpq-dev \
    gcc \
    python3-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome/Chromium options for running in container
ENV CHROMIUM_FLAGS="--no-sandbox --headless --disable-gpu --disable-software-rasterizer --disable-dev-shm-usage"

# Set up working directory
WORKDIR /app

# Set up Python virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN . /app/venv/activate && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run database setup and start the application
CMD ["/app/venv/bin/python", "main.py"]