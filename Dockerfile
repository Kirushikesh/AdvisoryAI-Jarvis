# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project (needed for local package install)
COPY . .

# Install the package and its dependencies
RUN pip install --no-cache-dir .

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.jarvis.api:app", "--host", "0.0.0.0", "--port", "8000"]
