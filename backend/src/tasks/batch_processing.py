"""
Celery tasks for batch processing of financial reports.

Handles async processing of batch report jobs and individual report processing.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from celery import Task, current_task
from sqlalchemy.orm import Session

from ..core.celery_app import celery_app
from ..database.connection import get_db_session_context
from ..models.financial_report import FinancialReport, ProcessingStatus
from ..models.user import User
from ..services.document_processor import DocumentProcessor, ProcessingResult
from ..services.batch_processor import BatchProcessor, BatchStatus

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Celery task base class that provides database session management."""
    
    _db: Optional[Session] = None
    
    @property
    def db(self) -> Session:
        """Get database session with context manager."""
        if self._db is None:
            self._db = next(get_db_session_context())
        return self._db
    
    def after_return(self, *args, **kwargs):
        """Clean up database session after task completion."""
        if self._db is not None:
            try:
                self._db.close()
            except Exception:
                pass
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask, name="backend.src.tasks.batch_processing.process_batch_reports")
def process_batch_reports(
    self: DatabaseTask,
    batch_id: str,
    user_id: str,
    report_ids: List[str],
    max_reports: int = 10
) -> Dict[str, Any]:
    """
    Process a batch of reports asynchronously.
    
    Args:
        batch_id: Unique batch job identifier
        user_id: UUID of user requesting batch processing
        report_ids: List of report UUID strings to process
        max_reports: Maximum number of reports allowed in batch
        
    Returns:
        Dictionary with batch processing results
    """
    try:
        logger.info(f"Starting batch processing for batch_id={batch_id}, reports={len(report_ids)}")
        
        # Validate batch size
        if len(report_ids) > max_reports:
            raise ValueError(
                f"Batch size ({len(report_ids)}) exceeds maximum limit ({max_reports})"
            )
        
        # Convert string IDs to UUIDs
        user_uuid = uuid.UUID(user_id)
        report_uuids = [uuid.UUID(rid) for rid in report_ids]
        
        # Get database session
        db = self.db
        
        # Get user to check subscription tier limits
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check user's batch limit
        user_batch_limit = user.get_batch_limit()
        if len(report_ids) > user_batch_limit:
            raise ValueError(
                f"Batch size ({len(report_ids)}) exceeds user's subscription limit ({user_batch_limit})"
            )
        
        # Fetch reports
        reports = db.query(FinancialReport).filter(
            FinancialReport.id.in_(report_uuids)
        ).all()
        
        if len(reports) != len(report_ids):
            found_ids = {str(r.id) for r in reports}
            missing_ids = [rid for rid in report_ids if rid not in found_ids]
            raise ValueError(f"Some reports not found: {missing_ids}")
        
        # Update all reports to PROCESSING status
        for report in reports:
            report.processing_status = ProcessingStatus.PROCESSING
        db.commit()
        
        # Update task state
        self.update_state(
            state="PROCESSING",
            meta={
                "batch_id": batch_id,
                "total_reports": len(reports),
                "processed": 0,
                "successful": 0,
                "failed": 0
            }
        )
        
        # Initialize document processor
        document_processor = DocumentProcessor()
        
        # Process reports
        results = []
        successful_count = 0
        failed_count = 0
        
        for i, report in enumerate(reports):
            try:
                # Update progress
                self.update_state(
                    state="PROCESSING",
                    meta={
                        "batch_id": batch_id,
                        "total_reports": len(reports),
                        "processed": i + 1,
                        "current_report": str(report.id),
                        "successful": successful_count,
                        "failed": failed_count
                    }
                )
                
                logger.info(f"Processing report {i+1}/{len(reports)}: {report.id}")
                
                # Process report
                result = document_processor.process_financial_report(report)
                
                # Update report status based on result
                if result.is_successful():
                    report.processing_status = ProcessingStatus.COMPLETED
                    report.processed_at = datetime.now(timezone.utc)
                    successful_count += 1
                else:
                    report.processing_status = ProcessingStatus.FAILED
                    failed_count += 1
                
                results.append({
                    "report_id": str(report.id),
                    "status": "success" if result.is_successful() else "failed",
                    "errors": result.errors if result.errors else [],
                    "analysis_id": str(result.analysis_id) if result.analysis_id else None
                })
                
            except Exception as e:
                logger.error(f"Error processing report {report.id}: {e}")
                # Mark report as failed
                report.processing_status = ProcessingStatus.FAILED
                failed_count += 1
                
                results.append({
                    "report_id": str(report.id),
                    "status": "failed",
                    "errors": [str(e)],
                    "analysis_id": None
                })
            
            # Commit after each report
            db.commit()
        
        # Determine overall batch status
        if successful_count == len(reports):
            batch_status = BatchStatus.COMPLETED.value
        elif successful_count == 0:
            batch_status = BatchStatus.FAILED.value
        else:
            batch_status = BatchStatus.PARTIALLY_COMPLETED.value
        
        result = {
            "batch_id": batch_id,
            "status": batch_status,
            "total_reports": len(reports),
            "successful": successful_count,
            "failed": failed_count,
            "results": results,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Batch processing completed: {batch_id}, status={batch_status}")
        
        return result
        
    except Exception as e:
        logger.error(f"Batch processing failed for {batch_id}: {e}", exc_info=True)
        # Update task state to FAILURE
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "batch_id": batch_id
            }
        )
        raise


@celery_app.task(bind=True, base=DatabaseTask, name="backend.src.tasks.batch_processing.process_single_report")
def process_single_report(
    self: DatabaseTask,
    report_id: str
) -> Dict[str, Any]:
    """
    Process a single report asynchronously.
    
    Args:
        report_id: UUID string of report to process
        
    Returns:
        Dictionary with processing result
    """
    try:
        logger.info(f"Processing single report: {report_id}")
        
        # Convert string ID to UUID
        report_uuid = uuid.UUID(report_id)
        
        # Get database session
        db = self.db
        
        # Get report
        report = db.query(FinancialReport).filter(
            FinancialReport.id == report_uuid
        ).first()
        
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Update report status to PROCESSING
        report.processing_status = ProcessingStatus.PROCESSING
        db.commit()
        
        # Process report
        document_processor = DocumentProcessor()
        result = document_processor.process_financial_report(report)
        
        # Update report status based on result
        if result.is_successful():
            report.processing_status = ProcessingStatus.COMPLETED
            report.processed_at = datetime.now(timezone.utc)
            status = "success"
        else:
            report.processing_status = ProcessingStatus.FAILED
            status = "failed"
        
        db.commit()
        
        return {
            "report_id": report_id,
            "status": status,
            "analysis_id": str(result.analysis_id) if result.analysis_id else None,
            "errors": result.errors if result.errors else [],
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Single report processing failed for {report_id}: {e}", exc_info=True)
        raise

