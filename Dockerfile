# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc
# PYTHONUNBUFFERED: Prevents Python from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# gcc and libpq-dev are often needed for psycopg2 compilation if using the non-binary version,
# but since we use psycopg2-binary, we might get away with just basic libs.
# However, it's safe to have netcat or other utils if needed for healthchecks.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose port 8000 (standard for FastAPI/Uvicorn)
EXPOSE 8000

# Run the command to start the application
# We use shell form to allow variable expansion if needed, but array form is preferred.
# Using array form with gunicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]
