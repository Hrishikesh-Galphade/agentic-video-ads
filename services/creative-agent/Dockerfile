# Start with an official Python 3.11 slim image
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

COPY ./src ./src

# This service will run on port 8001 to avoid conflicts
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]