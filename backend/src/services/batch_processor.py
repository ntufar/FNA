"""Batch processing service for financial reports.

Handles batch processing of multiple reports with limits, status tracking,
and progress updates.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.financial_report import FinancialReport, ProcessingStatus, ReportType
from ..models.narrative_analysis import NarrativeAnalysis
from ..models.user import User
from .document_processor import DocumentProcessor, ProcessingResult


class BatchStatus(str, Enum):
    """Status of a batch processing job."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"


class BatchProcessor:
    """Service for processing multiple financial reports in batch."""
    
    def __init__(self, db: Session):
        """Initialize batch processor.
        
        Args:
            db: Database session
        """
        self.db = db
        self.document_processor = DocumentProcessor()
    
    def process_batch(
        self,
        user_id: uuid.UUID,
        report_ids: List[uuid.UUID],
        max_reports: int = 10
    ) -> Dict[str, Any]:
        """Process a batch of reports.
        
        Args:
            user_id: ID of user requesting batch processing
            report_ids: List of report IDs to process
            max_reports: Maximum number of reports allowed (default 10)
            
        Returns:
            Dictionary with batch processing results
            
        Raises:
            ValueError: If batch exceeds maximum limit
        """
        # Validate batch size
        if len(report_ids) > max_reports:
            raise ValueError(
                f"Batch size ({len(report_ids)}) exceeds maximum limit ({max_reports})"
            )
        
        # Get user to check subscription tier limits
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check user's batch limit
        user_batch_limit = user.get_batch_limit()
        if len(report_ids) > user_batch_limit:
            raise ValueError(
                f"Batch size ({len(report_ids)}) exceeds user's subscription limit ({user_batch_limit})"
            )
        
        # Fetch reports
        reports = self.db.query(FinancialReport).filter(
            FinancialReport.id.in_(report_ids)
        ).all()
        
        if len(reports) != len(report_ids):
            found_ids = {str(r.id) for r in reports}
            missing_ids = [str(rid) for rid in report_ids if str(rid) not in found_ids]
            raise ValueError(f"Some reports not found: {missing_ids}")
        
        # Update all reports to PROCESSING status
        for report in reports:
            report.processing_status = ProcessingStatus.PROCESSING
        self.db.commit()
        
        # Process reports
        results = []
        successful_count = 0
        failed_count = 0
        
        for i, report in enumerate(reports):
            try:
                # Process report
                result = self.document_processor.process_financial_report(report)
                
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
            self.db.commit()
        
        # Determine overall batch status
        if successful_count == len(reports):
            batch_status = BatchStatus.COMPLETED
        elif successful_count == 0:
            batch_status = BatchStatus.FAILED
        else:
            batch_status = BatchStatus.PARTIALLY_COMPLETED
        
        return {
            "batch_id": str(uuid.uuid4()),
            "status": batch_status.value,
            "total_reports": len(reports),
            "successful": successful_count,
            "failed": failed_count,
            "results": results,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
    
    def get_batch_status(
        self,
        report_ids: List[uuid.UUID]
    ) -> Dict[str, Any]:
        """Get status of reports in a batch.
        
        Args:
            report_ids: List of report IDs to check
            
        Returns:
            Dictionary with batch status information
        """
        reports = self.db.query(FinancialReport).filter(
            FinancialReport.id.in_(report_ids)
        ).all()
        
        status_counts = {}
        results = []
        
        for report in reports:
            status = report.processing_status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Get analysis if completed
            analysis = None
            if report.processing_status == ProcessingStatus.COMPLETED:
                analysis = self.db.query(NarrativeAnalysis).filter(
                    NarrativeAnalysis.report_id == report.id
                ).first()
            
            results.append({
                "report_id": str(report.id),
                "status": status,
                "processed_at": report.processed_at.isoformat() if report.processed_at else None,
                "analysis_id": str(analysis.id) if analysis else None
            })
        
        # Determine overall status
        if all(r["status"] == "COMPLETED" for r in results):
            overall_status = BatchStatus.COMPLETED.value
        elif all(r["status"] == "FAILED" for r in results):
            overall_status = BatchStatus.FAILED.value
        elif any(r["status"] == "PROCESSING" for r in results):
            overall_status = BatchStatus.PROCESSING.value
        else:
            overall_status = BatchStatus.PARTIALLY_COMPLETED.value
        
        return {
            "status": overall_status,
            "total_reports": len(reports),
            "status_counts": status_counts,
            "results": results
        }

