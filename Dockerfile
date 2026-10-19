# ─────────────────────────────────────────────────────────────────────────────
# DompetIN — Personal Finance Manager
# Docker Image Build
# Base: python:3.11-slim (lightweight, compatible with all packages)
# Server: gunicorn (production WSGI server)
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest first (leverages Docker layer caching)
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application source code
COPY . .

# Create a dedicated directory for persistent data (SQLite DB lives here)
RUN mkdir -p /app/data

# Set environment variable so the app stores its DB in the persistent volume path
ENV DB_PATH=/app/data/database.db

# Expose the application port
EXPOSE 5000

# Health check: verify the app is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

# Start the application with gunicorn (binds to 0.0.0.0 by default)
# - 2 workers for single-core container
# - bind to all interfaces so Docker port mapping works
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
