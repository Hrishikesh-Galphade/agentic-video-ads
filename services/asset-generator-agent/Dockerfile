FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

COPY ./src ./src

# The command to start a Celery worker
CMD ["celery", "-A", "src.celery_app:celery", "worker", "--loglevel=info", "-Q", "asset_queue"]