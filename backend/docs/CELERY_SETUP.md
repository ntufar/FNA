# Celery Async Job Queue Setup

This guide explains how to set up and run Celery workers for async batch processing in the FNA platform.

## Overview

Celery is used for asynchronous processing of batch report jobs. This allows the API to return immediately while processing happens in the background. The system uses **PostgreSQL** as both the message broker and result backend, eliminating the need for additional infrastructure like Redis.

## Prerequisites

1. **PostgreSQL Database**: Already configured for FNA platform (Celery uses the same database)
2. **Python Environment**: All backend dependencies installed
3. **Database Migrations**: Run Alembic migrations to ensure database schema is up to date

## Architecture

- **Broker**: PostgreSQL (via SQLAlchemy transport)
- **Result Backend**: PostgreSQL (database backend)
- **No Additional Services**: Uses existing PostgreSQL database - no Redis or RabbitMQ needed

## Environment Variables

Celery uses the same database URL as the application. Configure in `.env`:

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/fna_development
```

The Celery configuration automatically uses this database URL for both broker and backend.

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

## Database Schema

Celery automatically creates necessary tables in PostgreSQL:
- `celery_taskmeta`: Stores task results
- `celery_tasksetmeta`: Stores task set results
- `kombu_message`: Stores queued messages (broker)

These tables are managed automatically by Celery/Kombu.

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

1. Check PostgreSQL is running and accessible
2. Verify database URL in environment
3. Check Python path: Ensure `backend/src` is in PYTHONPATH
4. Verify database connection: Test with `psql` or database client

### Tasks Not Processing

1. Check worker logs for errors
2. Verify queues match between worker and task routing
3. Check database connection: Ensure PostgreSQL is accessible
4. Verify Celery tables exist: Check `celery_taskmeta` and `kombu_message` tables

### Task Timeout Errors

- Increase `task_time_limit` in `celery_app.py`
- Check document processing time (should be < 60s per report)
- Consider processing fewer reports per batch

### Database Connection Issues

If you see connection errors:
1. Verify PostgreSQL is running
2. Check database credentials in `.env`
3. Ensure database exists and is accessible
4. Check connection pool settings if needed

## Advantages of PostgreSQL Backend

✅ **No Additional Infrastructure**: Uses existing PostgreSQL database  
✅ **Simpler Deployment**: No Redis or RabbitMQ to install and maintain  
✅ **Transactional**: Job creation and status updates are transactional  
✅ **Easy Debugging**: All data in one database, easy to query  
✅ **Unified Monitoring**: Monitor both application and task queue in one place  

## Limitations

⚠️ **Performance**: PostgreSQL broker may be slower than dedicated message queues for high-throughput scenarios  
⚠️ **Scalability**: For very high-volume processing, consider dedicated message broker (Redis/RabbitMQ)  
⚠️ **Database Load**: Task queue adds load to PostgreSQL database  

For most use cases, PostgreSQL as broker/backend is sufficient and simplifies deployment.

## Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/celery-worker.service`:

```ini
[Unit]
Description=Celery Worker for FNA Platform
After=network.target postgresql.service

[Service]
Type=forking
User=fna
Group=fna
WorkingDirectory=/opt/fna/backend
Environment="PATH=/opt/fna/venv/bin"
Environment="DATABASE_URL=postgresql://postgres:password@localhost:5432/fna"
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
      - DATABASE_URL=postgresql://postgres:password@db:5432/fna
    depends_on:
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

### Database Queries

Monitor tasks directly via PostgreSQL:

```sql
-- Check pending tasks
SELECT * FROM kombu_message WHERE visible = true;

-- Check task results
SELECT * FROM celery_taskmeta ORDER BY date_done DESC LIMIT 10;

-- Check task status
SELECT task_id, status, result, date_done 
FROM celery_taskmeta 
WHERE task_id = 'your-task-id';
```

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

### Database Optimization

For high-volume task processing:
- Ensure PostgreSQL has adequate resources
- Consider separate database for task queue if needed
- Monitor database connection pool usage
- Index Celery tables if needed

---

**See Also:**
- [Celery Documentation](https://docs.celeryproject.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [API Documentation](../../docs/api/README.md)

