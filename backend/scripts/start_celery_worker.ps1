# PowerShell script to start Celery worker for FNA platform batch processing

# Set environment variables
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
if (-not $env:ENVIRONMENT) {
    $env:ENVIRONMENT = "development"
}

# Default values
if (-not $env:QUEUES) {
    $env:QUEUES = "batch_processing,report_processing,default"
}
if (-not $env:CONCURRENCY) {
    $env:CONCURRENCY = "4"
}
if (-not $env:LOGLEVEL) {
    $env:LOGLEVEL = "info"
}

# Start Celery worker
celery -A backend.src.core.celery_app:celery_app worker `
  --loglevel="$env:LOGLEVEL" `
  --queues="$env:QUEUES" `
  --concurrency="$env:CONCURRENCY" `
  --autoreload

