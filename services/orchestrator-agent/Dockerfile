# Start with an official Python 3.11 slim image
FROM python:3.11-slim

# Set the working directory inside the container to /app
WORKDIR /app

# --- THIS IS THE FIX ---
# Add the working directory to the PYTHONPATH.
# This tells the Python interpreter to look for modules in the /app directory.
ENV PYTHONPATH=/app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
# --no-cache-dir makes the image smaller
# --trusted-host is a good practice for reliability in some network environments
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# Copy the entire 'src' directory from our host into the container's working directory
COPY ./src ./src

# The command to run when the container starts.
# This tells uvicorn to run the 'app' object from the 'src.main' module.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]