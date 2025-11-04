# Batch Processing Setup

This guide explains how batch processing works in the FNA platform using PostgreSQL-backed task queue.

## Overview

Batch processing uses **FastAPI BackgroundTasks** with **PostgreSQL** for job tracking. This eliminates the need for external message brokers like Redis or RabbitMQ. The system uses your existing PostgreSQL database - no additional software installation required.

## Architecture

- **Task Queue**: PostgreSQL `batch_jobs` table
- **Background Processing**: FastAPI BackgroundTasks (runs in same process)
- **Status Tracking**: Real-time updates in `batch_jobs` table
- **No External Dependencies**: Uses existing PostgreSQL database

## Prerequisites

1. **PostgreSQL Database**: Already configured for FNA platform
2. **Python Environment**: All backend dependencies installed
3. **Database Migration**: Run Alembic migrations to create `batch_jobs` table

## Database Setup

### Run Migration

```bash
# From backend directory
alembic upgrade head
```

This creates the `batch_jobs` table with the following structure:
- `batch_id`: Unique identifier for each batch job
- `user_id`: User who requested the batch
- `status`: Current status (PENDING, PROCESSING, COMPLETED, FAILED, PARTIALLY_COMPLETED)
- `total_reports`, `successful`, `failed`: Progress tracking
- `results`: JSON array with processing results
- `report_ids`: JSON array of report IDs to process

## How It Works

1. **API Request**: User submits batch via `POST /v1/reports/batch`
2. **Database Record**: Batch job created in `batch_jobs` table with status `PENDING`
3. **Background Task**: FastAPI BackgroundTasks queues the processing job
4. **Processing**: Background task processes reports sequentially
5. **Status Updates**: Job status and results updated in database
6. **Status Query**: User checks status via `GET /v1/reports/batch/{batch_id}`

## API Usage

### Submit Batch Job

```bash
POST /v1/reports/batch
Authorization: Bearer <token>
Content-Type: application/json

{
  "report_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Response:**
```json
{
  "batch_id": "batch-uuid",
  "status": "PENDING",
  "total_reports": 3,
  "successful": 0,
  "failed": 0,
  "results": [],
  "processed_at": null
}
```

### Check Batch Status

```bash
GET /v1/reports/batch/{batch_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "batch_id": "batch-uuid",
  "status": "PROCESSING",
  "total_reports": 3,
  "successful": 1,
  "failed": 0,
  "results": [
    {
      "report_id": "uuid1",
      "status": "success",
      "analysis_id": "analysis-uuid",
      "errors": []
    }
  ],
  "processed_at": "2025-01-27T10:30:00Z"
}
```

## Status Values

- **PENDING**: Batch job created, waiting to start processing
- **PROCESSING**: Currently processing reports
- **COMPLETED**: All reports processed successfully
- **FAILED**: All reports failed to process
- **PARTIALLY_COMPLETED**: Some reports succeeded, some failed

## Batch Limits

Batch size is limited by subscription tier:
- **Basic**: 3 reports max
- **Pro**: 7 reports max
- **Enterprise**: 10 reports max

## Troubleshooting

### Batch Not Processing

1. **Check Application Logs**: Look for errors in background task execution
2. **Check Database**: Verify `batch_jobs` table exists and has records
3. **Check Report Status**: Verify reports exist and are in `PENDING` status

```sql
-- Check batch job status
SELECT batch_id, status, total_reports, successful, failed 
FROM batch_jobs 
WHERE batch_id = 'your-batch-id';

-- Check report status
SELECT id, processing_status 
FROM financial_reports 
WHERE id IN ('report-id-1', 'report-id-2');
```

### Batch Stuck in PROCESSING

If a batch job is stuck in `PROCESSING` status:

1. Check application logs for errors
2. Verify the FastAPI application is running
3. Manually update status if needed (with caution):

```sql
-- Only if absolutely necessary
UPDATE batch_jobs 
SET status = 'FAILED', updated_at = NOW() 
WHERE batch_id = 'stuck-batch-id' AND status = 'PROCESSING';
```

### Performance Issues

- **Batch Size**: Reduce batch size if processing takes too long
- **Concurrent Requests**: Limit concurrent batch requests
- **Database Performance**: Ensure PostgreSQL has adequate resources

## Advantages Over Celery/Redis

✅ **No External Dependencies**: Uses existing PostgreSQL database  
✅ **Simpler Setup**: No Redis installation or configuration  
✅ **Easier Debugging**: All data in one database, easy to query  
✅ **Transactional**: Job creation and status updates are transactional  
✅ **No Message Broker**: Eliminates potential point of failure  

## Limitations

⚠️ **Same Process**: BackgroundTasks run in the same process as the API  
⚠️ **Not Distributed**: Cannot scale workers across multiple machines  
⚠️ **Process Restart**: Background tasks lost if API process restarts  

For production workloads requiring distributed processing, consider:
- Separate worker process that polls `batch_jobs` table
- Message queue system (Redis, RabbitMQ) if needed
- Container orchestration for horizontal scaling

## Production Deployment

### Monitoring

Monitor batch processing via database queries:

```sql
-- Active batch jobs
SELECT batch_id, status, total_reports, successful, failed, created_at
FROM batch_jobs
WHERE status IN ('PENDING', 'PROCESSING')
ORDER BY created_at DESC;

-- Batch job statistics
SELECT 
    status,
    COUNT(*) as count,
    AVG(total_reports) as avg_reports,
    AVG(successful) as avg_successful
FROM batch_jobs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY status;
```

### Cleanup

Periodically clean up old batch job records:

```sql
-- Delete completed jobs older than 30 days
DELETE FROM batch_jobs
WHERE status IN ('COMPLETED', 'FAILED')
AND processed_at < NOW() - INTERVAL '30 days';
```

---

**See Also:**
- [FastAPI BackgroundTasks Documentation](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [API Documentation](../../docs/api/README.md)


