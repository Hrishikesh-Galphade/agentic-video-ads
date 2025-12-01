# Start with an official Python 3.11 slim image. The 'slim' version is based on Debian.
FROM python:3.11-slim

# --- INSTALL SYSTEM DEPENDENCIES ---
# We need to install FFmpeg using the system's package manager (apt).
# 'apt-get update' refreshes the list of available packages.
# 'apt-get install -y ffmpeg' installs FFmpeg. The '-y' flag auto-confirms the installation.
# 'rm -rf /var/lib/apt/lists/*' cleans up the package list cache to keep the image smaller.
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container to /app
WORKDIR /app

# Add the working directory to the PYTHONPATH so Python can find our 'src' module
ENV PYTHONPATH=/app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies from requirements.txt
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# Copy the entire 'src' directory from our host into the container's working directory
COPY ./src ./src
COPY ./assets ./assets

# The command to run when the container starts.
# This starts a Celery worker that will listen for post-production tasks.
CMD ["celery", "-A", "src.celery_app:celery", "worker", "--loglevel=info", "-Q", "post_production_queue"]