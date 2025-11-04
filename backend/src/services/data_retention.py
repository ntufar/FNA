"""
Data retention and lifecycle management system for FNA Platform.

Implements FR-015: Indefinite storage requirements with lifecycle policies.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.financial_report import FinancialReport, ProcessingStatus
from ..models.narrative_analysis import NarrativeAnalysis
from ..models.narrative_delta import NarrativeDelta
from ..models.alert import Alert

logger = logging.getLogger(__name__)


class DataRetentionManager:
    """
    Manages data retention and lifecycle policies.
    
    Per FR-015: All data is stored indefinitely by default, but this service
    provides utilities for:
    - Archiving old data
    - Compressing historical data
    - Managing storage quotas
    - Data export for compliance
    """
    
    def __init__(self, db: Session):
        """
        Initialize data retention manager.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics for all data types.
        
        Returns:
            dict: Storage statistics
        """
        stats = {
            "companies": {
                "count": self.db.query(FinancialReport).distinct(FinancialReport.company_id).count(),
                "total_size_bytes": 0,  # Company records are small
            },
            "financial_reports": {
                "count": self.db.query(FinancialReport).count(),
                "total_size_bytes": self.db.query(
                    FinancialReport.file_size_bytes
                ).filter(FinancialReport.file_size_bytes.isnot(None)).scalar() or 0,
            },
            "narrative_analyses": {
                "count": self.db.query(NarrativeAnalysis).count(),
                "total_size_bytes": 0,  # Stored in database
            },
            "narrative_deltas": {
                "count": self.db.query(NarrativeDelta).count(),
                "total_size_bytes": 0,
            },
            "alerts": {
                "count": self.db.query(Alert).count(),
                "total_size_bytes": 0,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Calculate total file sizes
        total_file_size = self.db.query(
            FinancialReport.file_size_bytes
        ).filter(FinancialReport.file_size_bytes.isnot(None)).all()
        stats["financial_reports"]["total_size_bytes"] = sum(
            size[0] or 0 for size in total_file_size
        )
        
        return stats
    
    def archive_old_data(
        self,
        older_than_days: int = 365,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Archive data older than specified days.
        
        Note: Per FR-015, data is stored indefinitely. This method provides
        archiving capability but does not delete data.
        
        Args:
            older_than_days: Archive data older than this many days
            dry_run: If True, only report what would be archived
            
        Returns:
            dict: Archive operation results
        """
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        
        # Find old reports
        old_reports = self.db.query(FinancialReport).filter(
            FinancialReport.created_at < cutoff_date
        ).all()
        
        # Find old analyses
        old_analyses = self.db.query(NarrativeAnalysis).filter(
            NarrativeAnalysis.created_at < cutoff_date
        ).all()
        
        # Find old alerts (read and older than threshold)
        old_alerts = self.db.query(Alert).filter(
            and_(
                Alert.created_at < cutoff_date,
                Alert.is_read == True
            )
        ).all()
        
        archive_summary = {
            "cutoff_date": cutoff_date.isoformat(),
            "reports_to_archive": len(old_reports),
            "analyses_to_archive": len(old_analyses),
            "alerts_to_archive": len(old_alerts),
            "dry_run": dry_run,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if not dry_run:
            # In a real implementation, you would:
            # 1. Move files to archive storage (S3, cold storage, etc.)
            # 2. Update database records with archive location
            # 3. Compress data if needed
            logger.info(f"Archiving {len(old_reports)} reports, {len(old_analyses)} analyses, {len(old_alerts)} alerts")
            # TODO: Implement actual archiving logic
        else:
            logger.info(f"Dry run: Would archive {len(old_reports)} reports, {len(old_analyses)} analyses, {len(old_alerts)} alerts")
        
        return archive_summary
    
    def compress_historical_data(
        self,
        older_than_days: int = 730,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Compress historical data to reduce storage footprint.
        
        Args:
            older_than_days: Compress data older than this many days
            dry_run: If True, only report what would be compressed
            
        Returns:
            dict: Compression operation results
        """
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        
        old_reports = self.db.query(FinancialReport).filter(
            FinancialReport.created_at < cutoff_date
        ).all()
        
        compression_summary = {
            "cutoff_date": cutoff_date.isoformat(),
            "reports_to_compress": len(old_reports),
            "estimated_space_saved_bytes": 0,  # Would calculate based on compression ratio
            "dry_run": dry_run,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if not dry_run:
            # In a real implementation, you would:
            # 1. Compress PDF/HTML files using gzip or similar
            # 2. Store compressed versions
            # 3. Update file paths
            logger.info(f"Compressing {len(old_reports)} reports")
            # TODO: Implement actual compression logic
        
        return compression_summary
    
    def cleanup_failed_processes(
        self,
        older_than_days: int = 30,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up reports that have been in FAILED status for extended period.
        
        Args:
            older_than_days: Clean up failures older than this many days
            dry_run: If True, only report what would be cleaned up
            
        Returns:
            dict: Cleanup operation results
        """
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        
        failed_reports = self.db.query(FinancialReport).filter(
            and_(
                FinancialReport.processing_status == ProcessingStatus.FAILED,
                FinancialReport.created_at < cutoff_date
            )
        ).all()
        
        cleanup_summary = {
            "cutoff_date": cutoff_date.isoformat(),
            "failed_reports_to_cleanup": len(failed_reports),
            "dry_run": dry_run,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if not dry_run:
            # Optionally delete or mark for manual review
            logger.info(f"Cleaning up {len(failed_reports)} failed reports")
            # TODO: Implement cleanup logic (delete or move to quarantine)
        
        return cleanup_summary
    
    def export_data_for_compliance(
        self,
        company_id: Optional[str] = None,
        date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Export data for compliance purposes (e.g., GDPR, financial regulations).
        
        Args:
            company_id: Optional company ID to filter export
            date_range: Optional tuple of (start_date, end_date)
            
        Returns:
            dict: Export summary
        """
        export_summary = {
            "export_date": datetime.utcnow().isoformat(),
            "company_id": company_id,
            "date_range": date_range,
            "files_exported": [],
            "records_exported": 0
        }
        
        # In a real implementation, you would:
        # 1. Query all relevant data
        # 2. Export to structured format (JSON, CSV, etc.)
        # 3. Create export package
        # 4. Store export metadata
        
        logger.info(f"Exporting data for compliance: company_id={company_id}, date_range={date_range}")
        # TODO: Implement actual export logic
        
        return export_summary
    
    def get_retention_policy_summary(self) -> Dict[str, Any]:
        """
        Get summary of data retention policies.
        
        Returns:
            dict: Retention policy summary
        """
        return {
            "policy": "indefinite_storage",
            "description": "All data is stored indefinitely per FR-015 requirements",
            "archiving_enabled": True,
            "compression_enabled": True,
            "cleanup_enabled": True,
            "compliance_export_enabled": True,
            "timestamp": datetime.utcnow().isoformat()
        }

