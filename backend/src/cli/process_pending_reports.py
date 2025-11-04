"""
Command-line utility to process financial reports.

Usage examples:
  - Process PENDING (default):    python -m backend.src.cli.process_pending_reports
  - Process FAILED:               python -m backend.src.cli.process_pending_reports --status failed
  - Process PENDING and FAILED:   python -m backend.src.cli.process_pending_reports --status all
  - Limit to 5:                   python -m backend.src.cli.process_pending_reports --limit 5
  - Filter by company ticker:     python -m backend.src.cli.process_pending_reports --ticker AAPL
  - Process a specific report ID: python -m backend.src.cli.process_pending_reports --report-id <UUID>
  - Force reprocess COMPLETED:    python -m backend.src.cli.process_pending_reports --status all --force
"""

import argparse
import logging
import sys
import uuid
from datetime import datetime
from typing import Optional
import time

from ..database.connection import init_database, get_db_session_context
from ..models.financial_report import FinancialReport, ProcessingStatus
from ..models.company import Company
from ..services.document_processor import DocumentProcessor
from pathlib import Path

logger = logging.getLogger("process_pending_reports")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process pending financial reports")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ticker", type=str, help="Filter by company ticker symbol")
    group.add_argument("--company-id", type=str, help="Filter by company UUID")
    parser.add_argument("--report-id", type=str, help="Process a single report UUID")
    parser.add_argument("--limit", type=int, default=0, help="Max number of reports to process (0 = no limit)")
    parser.add_argument("--status", choices=["pending", "failed", "all"], default="pending", help="Which reports to target")
    parser.add_argument("--force", action="store_true", help="Force reprocess even if already completed")
    parser.add_argument("--watch", action="store_true", help="Continuously watch and process pending reports")
    parser.add_argument("--interval", type=int, default=15, help="Polling interval in seconds for --watch mode")
    return parser.parse_args()


def _fetch_reports(db, args: argparse.Namespace):
    # Build base query
    query = db.query(FinancialReport)

    # Specific report case
    if args.report_id:
        try:
            report_uuid = uuid.UUID(args.report_id)
        except ValueError:
            logger.error("--report-id is not a valid UUID")
            return []
        query = query.filter(FinancialReport.id == report_uuid)
    else:
        # Filter by requested status
        if args.status == "pending":
            query = query.filter(FinancialReport.processing_status == ProcessingStatus.PENDING)
        elif args.status == "failed":
            query = query.filter(FinancialReport.processing_status == ProcessingStatus.FAILED)
        else:  # all
            query = query.filter(FinancialReport.processing_status.in_([ProcessingStatus.PENDING, ProcessingStatus.FAILED]))

        # Optional company filters
        if args.company_id:
            try:
                company_uuid = uuid.UUID(args.company_id)
            except ValueError:
                logger.error("--company-id is not a valid UUID")
                return []
            query = query.filter(FinancialReport.company_id == company_uuid)
        elif args.ticker:
            company = db.query(Company).filter(Company.ticker_symbol == args.ticker.upper()).first()
            if not company:
                logger.error(f"No company found for ticker {args.ticker}")
                return []
            query = query.filter(FinancialReport.company_id == company.id)

    query = query.order_by(FinancialReport.created_at.asc())
    if args.limit and args.limit > 0:
        return query.limit(args.limit).all()
    return query.all()


def _process_reports(db, processor: DocumentProcessor, reports, force: bool) -> tuple[int, int]:
    processed = 0
    failures = 0
    for report in reports:
        try:
            logger.info(
                f"Processing report {report.id} for company="
                f"{report.company.ticker_symbol if report.company else report.company_id} "
                f"type={report.report_type.value} period={report.fiscal_period}"
            )

            # Ensure file exists
            file_path = Path(report.file_path)
            if not file_path.exists():
                logger.warning(f"File not found for report {report.id}: {file_path}")

            # Process the report
            result = processor.process_financial_report(report, include_embeddings=True, force_reprocess=force)

            # Save narrative analysis if created
            if result.narrative_analysis:
                db.add(result.narrative_analysis)
                # Flush to get the ID before adding embeddings
                db.flush()
                # Update embeddings with the correct analysis_id (they were created with None)
                for embedding in result.embeddings:
                    embedding.analysis_id = result.narrative_analysis.id
                    db.add(embedding)
                logger.info(f"Added narrative analysis {result.narrative_analysis.id} to database")
                if result.embeddings:
                    logger.info(f"Added {len(result.embeddings)} embeddings to database")

            # Update model status is handled in processor; ensure updated_at
            report.updated_at = datetime.utcnow()
            db.add(report)

            processed += 1
        except Exception as e:
            logger.exception(f"Failed to process report {report.id}: {e}")
            try:
                report.set_failed()
                report.updated_at = datetime.utcnow()
                db.add(report)
            except Exception:
                pass
            failures += 1
    return processed, failures


def main() -> int:
    args = parse_args()

    try:
        init_database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return 1

    processor = DocumentProcessor()

    if args.watch:
        logger.info(f"Starting watch mode (interval={args.interval}s) targeting status={args.status}")
        try:
            while True:
                with get_db_session_context() as db:
                    reports = _fetch_reports(db, args)
                    if reports:
                        logger.info(f"Found {len(reports)} report(s) to process")
                        processed, failures = _process_reports(db, processor, reports, args.force)
                        logger.info(f"Cycle complete. Successful: {processed}, Failed: {failures}")
                    else:
                        logger.info("No reports to process in this cycle")
                time.sleep(max(1, args.interval))
        except KeyboardInterrupt:
            logger.info("Watch mode interrupted by user. Exiting...")
            return 0
    else:
        with get_db_session_context() as db:
            reports = _fetch_reports(db, args)

            if not reports:
                logger.info("No reports to process")
                return 0

            logger.info(f"Found {len(reports)} report(s) to process")
            processed, failures = _process_reports(db, processor, reports, args.force)
            logger.info(f"Completed. Successful: {processed}, Failed: {failures}")
            return 0 if failures == 0 else 4


if __name__ == "__main__":
    sys.exit(main())


