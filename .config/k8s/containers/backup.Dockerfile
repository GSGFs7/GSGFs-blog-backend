# syntax=docker/dockerfile:1
# Backup image with PostgreSQL client tools and upload script

FROM python:3.14-slim

# Install PostgreSQL client and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    postgresql-common \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy upload script
COPY scripts/upload.py /app/

# Install Python dependencies
RUN pip install --no-cache-dir boto3 boto3-stubs[s3] python-dotenv

ENV PYTHONUNBUFFERED=1

# Set default command
CMD ["pg_dump", "--version"]
