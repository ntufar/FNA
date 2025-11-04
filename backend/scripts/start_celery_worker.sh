#!/bin/bash
# Start Celery worker for FNA platform batch processing

# Set environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export ENVIRONMENT="${ENVIRONMENT:-development}"

# Default values
QUEUES="${QUEUES:-batch_processing,report_processing,default}"
CONCURRENCY="${CONCURRENCY:-4}"
LOGLEVEL="${LOGLEVEL:-info}"

# Start Celery worker
celery -A backend.src.core.celery_app:celery_app worker \
  --loglevel="${LOGLEVEL}" \
  --queues="${QUEUES}" \
  --concurrency="${CONCURRENCY}" \
  --autoreload

