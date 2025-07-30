##
## Multi‑purpose Dockerfile for the skincare agent application.
##
## This Dockerfile builds a minimal container that serves the FastAPI backend
## and static frontend assets.  It installs Python dependencies and exposes
## port 8000.  The React application is static and does not require a Node
## runtime inside the container.

FROM python:3.11-slim as base

# Working directory inside the container
WORKDIR /app

# Copy backend requirements first to leverage Docker layer caching
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application source
COPY backend /app/backend
COPY frontend/public /app/frontend/public

# Expose the port used by uvicorn
EXPOSE 8000

# Set the default command to run the FastAPI application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
