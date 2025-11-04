# Celery Async Job Queue Setup

This guide explains how to set up and run Celery workers for async batch processing in the FNA platform.

## Overview

Celery is used for asynchronous processing of batch report jobs. This allows the API to return immediately while processing happens in the background.

## Prerequisites

1. **Redis Server**: Celery requires Redis as a message broker and result backend
2. **Python Environment**: All backend dependencies installed

## Redis Setup

### Install Redis

**Windows:**
- Download from: https://github.com/microsoftarchive/redis/releases
- Or use WSL with: `sudo apt-get install redis-server`

**Linux/macOS:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
```

### Start Redis

```bash
# Windows
redis-server

# Linux/macOS
sudo systemctl start redis
# or
redis-server
```

### Verify Redis is Running

```bash
redis-cli ping
# Should return: PONG
```

## Environment Variables

Configure Redis URL in `.env`:

```bash
REDIS_URL=redis://localhost:6379/0
```

## Running Celery Workers

### Start Worker for Batch Processing

```bash
# From backend directory
celery -A backend.src.core.celery_app:celery_app worker \
  --loglevel=info \
  --queues=batch_processing,report_processing,default \
  --concurrency=4
```

### Start Worker with Auto-reload (Development)

```bash
celery -A backend.src.core.celery_app:celery_app worker \
  --loglevel=info \
  --queues=batch_processing,report_processing,default \
  --concurrency=4 \
  --autoreload
```

### Monitor Tasks

```bash
# Start Flower (Celery monitoring tool)
celery -A backend.src.core.celery_app:celery_app flower
# Access at http://localhost:5555
```

## Task Queues

The system uses three queues:

1. **batch_processing**: For batch report processing jobs
2. **report_processing**: For individual report processing
3. **default**: General tasks

## Task Configuration

Tasks are configured in `backend/src/core/celery_app.py`:

- **Task timeout**: 1 hour hard limit, 55 minutes soft limit
- **Result expiration**: 1 hour
- **Worker prefetch**: 1 (prevents worker from grabbing too many tasks)
- **Max tasks per child**: 50 (recycles worker after 50 tasks)

## API Usage

### Submit Batch Job

```bash
POST /v1/reports/batch
{
  "report_ids": ["uuid1", "uuid2", "uuid3"]
}
```

Response includes `task_id` for status tracking:

```json
{
  "batch_id": "batch-uuid",
  "status": "PROCESSING",
  "task_id": "celery-task-id",
  ...
}
```

### Check Batch Status

```bash
GET /v1/reports/batch/{batch_id}?task_id={celery-task-id}
```

## Troubleshooting

### Worker Not Starting

1. Check Redis is running: `redis-cli ping`
2. Verify Redis URL in environment
3. Check Python path: Ensure `backend/src` is in PYTHONPATH

### Tasks Not Processing

1. Check worker logs for errors
2. Verify queues match between worker and task routing
3. Check Redis connection: `redis-cli monitor`

### Task Timeout Errors

- Increase `task_time_limit` in `celery_app.py`
- Check document processing time (should be < 60s per report)
- Consider processing fewer reports per batch

## Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/celery-worker.service`:

```ini
[Unit]
Description=Celery Worker for FNA Platform
After=network.target redis.service

[Service]
Type=forking
User=fna
Group=fna
WorkingDirectory=/opt/fna/backend
Environment="PATH=/opt/fna/venv/bin"
ExecStart=/opt/fna/venv/bin/celery -A backend.src.core.celery_app:celery_app worker \
  --loglevel=info \
  --queues=batch_processing,report_processing,default \
  --concurrency=4 \
  --pidfile=/var/run/celery/worker.pid \
  --logfile=/var/log/celery/worker.log

[Install]
WantedBy=multi-user.target
```

### Docker Compose

```yaml
services:
  celery-worker:
    build: ./backend
    command: celery -A backend.src.core.celery_app:celery_app worker --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://postgres:password@db:5432/fna
    depends_on:
      - redis
      - db
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
```

## Monitoring

### Flower Dashboard

Flower provides a web UI for monitoring Celery:

```bash
pip install flower
celery -A backend.src.core.celery_app:celery_app flower
```

Access at: http://localhost:5555

### Logging

Worker logs include:
- Task start/completion
- Progress updates
- Error messages
- Performance metrics

## Performance Tuning

### Concurrency

Adjust based on CPU cores and memory:

```bash
--concurrency=4  # 4 parallel tasks
```

### Queue Routing

Balance load across queues:

```python
task_routes = {
    "batch_processing": {"queue": "batch_processing"},
    "single_reports": {"queue": "report_processing"},
}
```

### Result Backend

For high-throughput, consider separate Redis DB:

```python
broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/1"
```

---

**See Also:**
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/docs/)
- [API Documentation](../../docs/api/README.md)

