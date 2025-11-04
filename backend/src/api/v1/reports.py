"""Financial report endpoints for FNA backend API."""

import os
import uuid
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, validator, ConfigDict
from sqlalchemy.orm import Session

from ...core.security import get_current_user, require_pro_tier
from ...core.api_auth import get_current_user_or_api_key, require_api_access
from ...database.connection import get_db
from ...models.company import Company
from ...models.financial_report import FinancialReport, ReportType, FileFormat, ProcessingStatus, DownloadSource
from ...services.document_processor import DocumentProcessor
from ...services.company_lookup import get_official_name_from_ticker

router = APIRouter()
logger = logging.getLogger(__name__)

# Constants and configuration
UPLOAD_DIR = Path("uploads/reports")
ALLOWED_MIME_TYPES = {
    "application/pdf": FileFormat.PDF,
    "text/html": FileFormat.HTML,
    "application/xhtml+xml": FileFormat.HTML,
    "text/plain": FileFormat.TXT,
    "application/xml": FileFormat.IXBRL,
    "text/xml": FileFormat.IXBRL
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


# Helper functions
def ensure_upload_directory():
    """Ensure upload directory exists."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_file_format_from_mime_type(mime_type: str) -> FileFormat:
    """Get FileFormat enum from MIME type."""
    return ALLOWED_MIME_TYPES.get(mime_type, FileFormat.TXT)


def generate_file_path(company_id: str, filename: str) -> Path:
    """Generate a unique file path for uploaded report."""
    # Create company-specific subdirectory
    company_dir = UPLOAD_DIR / str(company_id)
    company_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(filename)
    unique_filename = f"{timestamp}_{name}{ext}"
    
    return company_dir / unique_filename


async def process_report_background(report_id: str):
    """Background task to process uploaded report via local LLM (http://127.0.0.1:1234)."""
    from ...database.connection import get_db_session_context  # type: ignore
    from ...models.financial_report import FinancialReport  # type: ignore
    from ...models.narrative_analysis import NarrativeAnalysis  # type: ignore
    from ...models.narrative_embedding import NarrativeEmbedding  # type: ignore

    try:
        processor = DocumentProcessor()

        # Open a DB session context for the whole processing transaction
        with get_db_session_context() as db:
            # Load report
            try:
                report_uuid = uuid.UUID(report_id)
            except ValueError:
                # Invalid report id, nothing to do
                return

            report: FinancialReport = db.query(FinancialReport).filter(FinancialReport.id == report_uuid).first()
            if not report:
                return

            # Run processing pipeline (extract text, analyze via local LLM, generate embeddings)
            processing_result = processor.process_financial_report(report, include_embeddings=True)

            # Persist results if successful
            if processing_result.narrative_analysis:
                analysis: NarrativeAnalysis = processing_result.narrative_analysis
                db.add(analysis)

            if processing_result.embeddings:
                for emb in processing_result.embeddings:
                    db.add(emb)

            # Report status changes are applied to report by processor; flush/commit handled by context
            # Ensure objects are flushed so IDs are available
            db.flush()

            # Nothing else; context manager will commit
    except Exception as e:
        # Best-effort logging; avoid crashing background task
        print(f"Error processing report {report_id}: {e}")


# Request/Response models
class ReportResponse(BaseModel):
    """Financial report response model."""
    id: str
    company_id: str
    company_name: Optional[str] = None
    ticker_symbol: Optional[str] = None
    report_type: str
    fiscal_period: Optional[str] = None
    filing_date: Optional[str] = None
    file_format: str
    file_size_bytes: Optional[int] = None
    download_source: str
    processing_status: str
    created_at: str
    processed_at: Optional[str] = None


class ReportUploadResponse(BaseModel):
    """Report upload response model."""
    report_id: str
    message: str
    processing_status: str
    file_path: Optional[str] = None
    estimated_processing_time: Optional[str] = None


class ReportUploadRequest(BaseModel):
    """Report upload form data model."""
    company_id: str
    report_type: str = "Other"
    fiscal_period: Optional[str] = None
    
    @validator('company_id')
    def validate_company_id(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid company ID format')
    
    @validator('report_type')
    def validate_report_type(cls, v):
        valid_types = ["10-K", "10-Q", "8-K", "Annual", "Other"]
        if v not in valid_types:
            raise ValueError(f'Report type must be one of: {", ".join(valid_types)}')
        return v


class SECDownloadRequest(BaseModel):
    """SEC.gov automatic download request."""
    ticker_symbol: str
    report_type: str = "10-K"
    fiscal_year: Optional[int] = None
    accession_number: Optional[str] = None
    filing_date: Optional[str] = None
    
    @validator('ticker_symbol')
    def validate_ticker_symbol(cls, v):
        if not v or len(v) < 1 or len(v) > 5:
            raise ValueError('Ticker symbol must be 1-5 characters')
        return v.upper()
    
    @validator('report_type')
    def validate_report_type(cls, v):
        valid_types = ["10-K", "10-Q", "8-K"]
        if v not in valid_types:
            raise ValueError(f'Report type must be one of: {", ".join(valid_types)}')
        return v


class AvailableFilingResponse(BaseModel):
    """Available SEC filing with download status."""
    accession_number: str
    filing_date: str
    fiscal_period: Optional[str]
    report_type: str
    is_downloaded: bool
    existing_report_id: Optional[str] = None
    file_format: str
    report_url: Optional[str] = None
class UpdateReportStatusRequest(BaseModel):
    """Request model to update the processing status of a report."""
    status: str

    @validator('status')
    def validate_status(cls, v):
        try:
            ProcessingStatus(v)
            return v
        except Exception:
            raise ValueError(f"Invalid status. Must be one of: {', '.join([s.value for s in ProcessingStatus])}")


class BatchProcessRequest(BaseModel):
    """Request model for batch processing reports."""
    report_ids: List[str]
    
    @validator('report_ids')
    def validate_report_ids(cls, v):
        if not v:
            raise ValueError("report_ids cannot be empty")
        if len(v) > 10:
            raise ValueError("Maximum 10 reports allowed per batch")
        # Validate UUID format
        for rid in v:
            try:
                uuid.UUID(rid)
            except ValueError:
                raise ValueError(f"Invalid report ID format: {rid}")
        return v


class BatchProcessResponse(BaseModel):
    """Response model for batch processing."""
    batch_id: str
    status: str
    total_reports: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    processed_at: str
    task_id: Optional[str] = None  # Celery task ID for status tracking



@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    company_id: str = None,
    report_type: str = None,
    status: str = None,
    skip: int = 0,
    limit: int | None = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List financial reports with optional filtering from the database."""
    query = db.query(FinancialReport).order_by(FinancialReport.filing_date.desc())
    
    # Filters
    if company_id:
        try:
            company_uuid = uuid.UUID(company_id)
            query = query.filter(FinancialReport.company_id == company_uuid)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid company ID format")
    if report_type:
        try:
            query = query.filter(FinancialReport.report_type == ReportType(report_type))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report type")
    if status:
        try:
            query = query.filter(FinancialReport.processing_status == ProcessingStatus(status))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    # Apply pagination only if a limit is explicitly provided; otherwise return all
    if limit is not None:
        query = query.offset(max(0, skip)).limit(max(1, min(int(limit), 500)))
    reports = query.all()

    results: List[ReportResponse] = []
    for r in reports:
        results.append(ReportResponse(
            id=str(r.id),
            company_id=str(r.company_id),
            company_name=r.company.company_name if r.company else None,
            ticker_symbol=r.company.ticker_symbol if r.company else None,
            report_type=r.report_type.value if r.report_type else "Other",
            fiscal_period=r.fiscal_period,
            filing_date=r.filing_date.isoformat() if r.filing_date else None,
            file_format=r.file_format.value if r.file_format else "TXT",
            file_size_bytes=r.file_size_bytes,
            download_source=r.download_source.value if r.download_source else "MANUAL_UPLOAD",
            processing_status=r.processing_status.value if r.processing_status else "PENDING",
            created_at=r.created_at.isoformat() if r.created_at else datetime.now(timezone.utc).isoformat(),
            processed_at=r.processed_at.isoformat() if r.processed_at else None,
        ))

    return results


@router.post("/upload", response_model=ReportUploadResponse)
async def upload_report(
    company_id: str = Form(...),
    report_type: str = Form("Other"),
    fiscal_period: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a financial report file for analysis."""
    
    # Validate company exists
    try:
        company_uuid = uuid.UUID(company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid company ID format"
        )
    
    company = db.query(Company).filter(Company.id == company_uuid).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Supported types: {', '.join(ALLOWED_MIME_TYPES.keys())}"
        )
    
    # Validate file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({len(file_content)} bytes) exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit"
        )
    
    # Ensure upload directory exists
    ensure_upload_directory()
    
    # Generate unique file path
    file_path = generate_file_path(company_id, file.filename)
    
    try:
        # Save file to disk
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        # Create database record
        new_report = FinancialReport(
            id=uuid.uuid4(),
            company_id=company_uuid,
            report_type=ReportType(report_type) if report_type in [e.value for e in ReportType] else ReportType.OTHER,
            fiscal_period=fiscal_period,
            filing_date=datetime.now(timezone.utc).date(),
            file_path=str(file_path),
            file_format=get_file_format_from_mime_type(file.content_type),
            file_size_bytes=len(file_content),
            download_source=DownloadSource.MANUAL_UPLOAD,
            processing_status=ProcessingStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        return ReportUploadResponse(
            report_id=str(new_report.id),
            message=f"File '{file.filename}' uploaded successfully and queued for processing",
            processing_status=ProcessingStatus.PENDING.value,
            file_path=str(file_path.relative_to(UPLOAD_DIR)),
            estimated_processing_time="2-5 minutes"
        )
        
    except Exception as e:
        # Cleanup file if database operation failed
        if file_path.exists():
            file_path.unlink()
        
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload and save report"
        )


@router.get("/available-filings", response_model=List[AvailableFilingResponse])
async def get_available_filings(
    ticker_symbol: str,
    report_type: str,
    fiscal_year: Optional[int] = None,
    current_user: Dict[str, Any] = Depends(require_pro_tier),
    db: Session = Depends(get_db)
):
    """Get available SEC filings for a company with download status checking.
    
    Requires Pro or Enterprise subscription.
    Fetches recent filings from SEC and checks which ones are already downloaded.
    """
    from ...services.sec_downloader import SECDownloader, SECAPIError
    
    # Validate report type
    if report_type not in ["10-K", "10-Q", "8-K"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report type. Must be one of: 10-K, 10-Q, 8-K"
        )
    
    # Validate ticker symbol
    if not ticker_symbol or len(ticker_symbol) < 1 or len(ticker_symbol) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker symbol must be 1-5 characters"
        )
    
    ticker_symbol = ticker_symbol.upper()
    
    try:
        # Initialize SEC downloader
        sec_downloader = SECDownloader()
        
        # Fetch filings from SEC (up to 20)
        sec_filings = sec_downloader.get_company_filings(
            ticker=ticker_symbol,
            form_types=[report_type],
            limit=20
        )
        
        # Check if filings exist in our database
        company = db.query(Company).filter(
            Company.ticker_symbol == ticker_symbol
        ).first()
        
        downloaded_accessions = set()
        downloaded_reports = {}
        
        if company:
            # Query existing reports for this company and report type
            existing_reports = db.query(FinancialReport).filter(
                FinancialReport.company_id == company.id,
                FinancialReport.report_type == ReportType(report_type)
            ).all()
            
            for report in existing_reports:
                if report.filing_date:
                    # Normalize filing dates for comparison
                    filing_date_str = report.filing_date.strftime("%Y-%m-%d")
                    downloaded_accessions.add(filing_date_str)
                    downloaded_reports[filing_date_str] = str(report.id)
        
        # Build response list
        results = []
        for filing in sec_filings:
            # Apply fiscal year filter if provided
            if fiscal_year and filing.filing_date:
                try:
                    filing_date_obj = datetime.strptime(filing.filing_date, "%Y-%m-%d").date()
                    if filing_date_obj.year != fiscal_year:
                        continue
                except (ValueError, AttributeError):
                    pass
            
            # Check if already downloaded
            is_downloaded = filing.filing_date in downloaded_accessions
            existing_report_id = downloaded_reports.get(filing.filing_date)
            
            # Infer fiscal period from filing date
            fiscal_period = None
            if filing.filing_date:
                try:
                    filing_date_obj = datetime.strptime(filing.filing_date, "%Y-%m-%d").date()
                    year = filing_date_obj.year
                    month = filing_date_obj.month
                    
                    if report_type in ["10-K", "Annual"]:
                        fiscal_period = f"FY {year}"
                    elif report_type == "10-Q":
                        quarter = 'Q1' if month in [1,2,3] else 'Q2' if month in [4,5,6] else 'Q3' if month in [7,8,9] else 'Q4'
                        fiscal_period = f"{quarter} {year}"
                    else:
                        fiscal_period = f"FY {year}"
                except (ValueError, AttributeError):
                    pass
            
            results.append(AvailableFilingResponse(
                accession_number=filing.accession_number,
                filing_date=filing.filing_date,
                fiscal_period=fiscal_period,
                report_type=filing.report_type,
                is_downloaded=is_downloaded,
                existing_report_id=existing_report_id,
                file_format=filing.file_format,
                report_url=filing.report_url
            ))
        
        return results
        
    except SECAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to fetch filings from SEC: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching available filings: {str(e)}"
        )


@router.post("/download", response_model=ReportUploadResponse)
async def download_from_sec(
    download_request: SECDownloadRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_pro_tier),
    db: Session = Depends(get_db)
):
    """Automatically download a report from SEC.gov.
    
    Requires Pro or Enterprise subscription.
    Downloads latest filing for the specified ticker and report type.
    If accession_number or filing_date is provided, downloads that specific filing instead.
    """
    from ...services.sec_downloader import SECDownloader
    
    # Find or create company
    company = db.query(Company).filter(
        Company.ticker_symbol == download_request.ticker_symbol
    ).first()
    
    if not company:
        # Auto-create company with official name from SEC if available
        official = get_official_name_from_ticker(download_request.ticker_symbol) or download_request.ticker_symbol
        company = Company(
            id=uuid.uuid4(),
            ticker_symbol=download_request.ticker_symbol,
            company_name=official,
            sector=None,
            industry=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(company)
        db.commit()
        db.refresh(company)
    
    try:
        # Initialize SEC downloader
        sec_downloader = SECDownloader()
        
        # Determine which filing to download
        if download_request.accession_number or download_request.filing_date:
            # Download specific filing
            download_result = await sec_downloader.download_specific_filing(
                ticker_symbol=download_request.ticker_symbol,
                report_type=download_request.report_type,
                accession_number=download_request.accession_number,
                filing_date=download_request.filing_date
            )
        else:
            # Download latest filing
            download_result = await sec_downloader.download_latest_filing(
                ticker_symbol=download_request.ticker_symbol,
                report_type=download_request.report_type,
                fiscal_year=download_request.fiscal_year
            )
        
        if not download_result['success']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=download_result.get('error', 'Failed to download report from SEC.gov')
            )
        
        # Check if report already exists before moving files
        filing_date = None
        if download_result.get('filing_date'):
            try:
                filing_date = datetime.fromisoformat(download_result['filing_date']).date()
            except (ValueError, AttributeError):
                pass
        
        if filing_date:
            existing_report = db.query(FinancialReport).filter(
                FinancialReport.company_id == company.id,
                FinancialReport.report_type == ReportType(download_request.report_type),
                FinancialReport.filing_date == filing_date
            ).first()
            
            if existing_report:
                # Clean up downloaded file since it's a duplicate
                try:
                    downloaded_file_path = Path(download_result['file_path'])
                    if downloaded_file_path.exists():
                        downloaded_file_path.unlink()
                except Exception:
                    pass
                
                # Return existing report info
                return ReportUploadResponse(
                    report_id=str(existing_report.id),
                    message=f"Report already exists for {download_request.ticker_symbol} ({download_request.report_type}) filed on {filing_date}",
                    processing_status=existing_report.processing_status.value if existing_report.processing_status else ProcessingStatus.PENDING.value,
                    file_path=str(Path(existing_report.file_path).relative_to(UPLOAD_DIR)) if existing_report.file_path else None,
                    estimated_processing_time=None
                )
        
        # Ensure upload directory exists
        ensure_upload_directory()
        
        # Generate file path for downloaded report
        original_filename = download_result['filename']
        file_path = generate_file_path(str(company.id), original_filename)
        
        # Move downloaded file to organized location
        downloaded_file_path = Path(download_result['file_path'])
        shutil.move(str(downloaded_file_path), str(file_path))
        
        # Infer fiscal period if missing from downloader
        inferred_fiscal_period = download_result.get('fiscal_period') or 'FY Unknown'
        if inferred_fiscal_period == 'FY Unknown':
            try:
                dt = datetime.fromisoformat(download_result['filing_date']) if download_result.get('filing_date') else None
                if dt is not None:
                    year = dt.year
                    rt = (download_request.report_type or '').upper()
                    if rt in ['10-K', '10-K/A', 'ANNUAL', 'TEN_K']:
                        inferred_fiscal_period = f"FY {year}"
                    elif rt in ['10-Q', '10-Q/A', 'TEN_Q']:
                        m = dt.month
                        quarter = 'Q1' if m in [1,2,3] else 'Q2' if m in [4,5,6] else 'Q3' if m in [7,8,9] else 'Q4'
                        inferred_fiscal_period = f"{quarter} {year}"
                    else:
                        inferred_fiscal_period = f"FY {year}"
            except Exception:
                inferred_fiscal_period = 'FY Unknown'

        # Create database record
        new_report = FinancialReport(
            id=uuid.uuid4(),
            company_id=company.id,
            report_type=ReportType(download_request.report_type),
            fiscal_period=inferred_fiscal_period,
            filing_date=datetime.fromisoformat(download_result['filing_date']) if download_result.get('filing_date') else None,
            report_url=download_result.get('report_url'),
            file_path=str(file_path),
            file_format=get_file_format_from_mime_type(download_result.get('content_type', 'text/html')),
            file_size_bytes=file_path.stat().st_size,
            download_source=DownloadSource.SEC_AUTO,
            processing_status=ProcessingStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        return ReportUploadResponse(
            report_id=str(new_report.id),
            message=f"SEC.gov report downloaded successfully for {download_request.ticker_symbol} ({download_request.report_type})",
            processing_status=ProcessingStatus.PENDING.value,
            file_path=str(file_path.relative_to(UPLOAD_DIR)),
            estimated_processing_time="3-7 minutes for SEC reports"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download report from SEC.gov: {str(e)}"
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific report from the database."""
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report ID format")

    r = db.query(FinancialReport).filter(FinancialReport.id == report_uuid).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return ReportResponse(
        id=str(r.id),
        company_id=str(r.company_id),
        company_name=r.company.company_name if r.company else None,
        ticker_symbol=r.company.ticker_symbol if r.company else None,
        report_type=r.report_type.value if r.report_type else "Other",
        fiscal_period=r.fiscal_period,
        filing_date=r.filing_date.isoformat() if r.filing_date else None,
        file_format=r.file_format.value if r.file_format else "TXT",
        file_size_bytes=r.file_size_bytes,
        download_source=r.download_source.value if r.download_source else "MANUAL_UPLOAD",
        processing_status=r.processing_status.value if r.processing_status else "PENDING",
        created_at=r.created_at.isoformat() if r.created_at else datetime.now(timezone.utc).isoformat(),
        processed_at=r.processed_at.isoformat() if r.processed_at else None,
    )


class AnalysisResponse(BaseModel):
    """Narrative analysis response model."""
    model_config = ConfigDict(protected_namespaces=('settings_',))
    
    id: str
    report_id: str
    optimism_score: float
    optimism_confidence: float
    risk_score: float
    risk_confidence: float
    uncertainty_score: float
    uncertainty_confidence: float
    key_themes: List[str]
    risk_indicators: List[Dict[str, Any]]
    narrative_sections: Dict[str, Any]
    financial_metrics: Optional[Dict[str, Any]] = None
    processing_time_seconds: Optional[int] = None
    model_version: str
    created_at: str


@router.get("/{report_id}/analysis", response_model=AnalysisResponse)
async def get_report_analysis(
    report_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get narrative analysis results for a report."""
    
    try:
        # Convert report_id to UUID format
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report ID format"
        )
    
    # Check if report exists
    report = db.query(FinancialReport).filter(FinancialReport.id == report_uuid).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Check if analysis is completed
    if report.processing_status == ProcessingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Analysis is still processing. Please try again later."
        )
    elif report.processing_status == ProcessingStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Analysis is currently in progress. Please try again later."
        )
    elif report.processing_status == ProcessingStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Analysis failed. Please try uploading the report again."
        )
    
    # Get analysis from database
    from ...models.narrative_analysis import NarrativeAnalysis
    analysis = db.query(NarrativeAnalysis).filter(
        NarrativeAnalysis.report_id == report_uuid
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found for this report"
        )
    
    return AnalysisResponse(
        id=str(analysis.id),
        report_id=str(analysis.report_id),
        optimism_score=analysis.optimism_score,
        optimism_confidence=analysis.optimism_confidence,
        risk_score=analysis.risk_score,
        risk_confidence=analysis.risk_confidence,
        uncertainty_score=analysis.uncertainty_score,
        uncertainty_confidence=analysis.uncertainty_confidence,
        key_themes=analysis.key_themes or [],
        risk_indicators=analysis.risk_indicators or [],
        narrative_sections=analysis.narrative_sections or {},
        financial_metrics=analysis.financial_metrics,
        processing_time_seconds=analysis.processing_time_seconds,
        model_version=analysis.model_version or "qwen3-4b-2507",
        created_at=analysis.created_at.isoformat()
    )


@router.post("/{report_id}/analyze")
async def reanalyze_report(
    report_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Re-run analysis for a report by resetting status only (processing via CLI)."""
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report ID format")

    report = db.query(FinancialReport).filter(FinancialReport.id == report_uuid).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Reset to pending only; CLI will perform processing
    report.reset_to_pending()
    report.updated_at = datetime.now(timezone.utc)
    db.add(report)
    db.commit()

    return {
        "report_id": report_id,
        "message": "Report status reset to PENDING. Use CLI to process.",
        "processing_status": ProcessingStatus.PENDING.value,
    }


@router.post("/batch", response_model=BatchProcessResponse)
async def batch_process_reports(
    batch_request: BatchProcessRequest,
    current_user: Dict[str, Any] = Depends(require_pro_tier),
    db: Session = Depends(get_db)
):
    """Process multiple reports in batch asynchronously using Celery.
    
    Requires Pro or Enterprise subscription. Batch size is limited by subscription tier:
    - Pro: 7 reports max
    - Enterprise: 10 reports max
    
    Returns immediately with batch_id for status tracking.
    Use GET /reports/batch/{batch_id} to check progress.
    """
    from ...core.celery_app import get_celery_app
    from ...tasks.batch_processing import process_batch_reports
    
    try:
        # Convert report IDs to UUIDs
        report_uuids = [uuid.UUID(rid) for rid in batch_request.report_ids]
        user_uuid = uuid.UUID(current_user["id"])
        
        # Generate batch ID
        batch_id = str(uuid.uuid4())
        
        # Submit batch job to Celery queue
        celery_app = get_celery_app()
        task = process_batch_reports.delay(
            batch_id=batch_id,
            user_id=str(user_uuid),
            report_ids=batch_request.report_ids,
            max_reports=10
        )
        
        # Return batch info immediately
        return BatchProcessResponse(
            batch_id=batch_id,
            status="PROCESSING",
            total_reports=len(batch_request.report_ids),
            successful=0,
            failed=0,
            results=[],
            processed_at=datetime.now(timezone.utc).isoformat(),
            task_id=task.id  # Include Celery task ID for status tracking
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing failed: {str(e)}"
        )


@router.get("/batch/{batch_id}", response_model=BatchProcessResponse)
async def get_batch_status(
    batch_id: str,
    task_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(require_pro_tier),
    db: Session = Depends(get_db)
):
    """Get status of a batch processing job.
    
    Returns current status and progress for an async batch job.
    If task_id is provided, queries Celery task status directly.
    Otherwise, falls back to querying reports by batch_id from database.
    """
    from ...core.celery_app import get_celery_app
    from ...services.batch_processor import BatchProcessor
    
    try:
        celery_app = get_celery_app()
        
        # If task_id provided, query Celery task status
        if task_id:
            try:
                task = celery_app.AsyncResult(task_id)
                task_state = task.state
                
                if task_state == "PENDING":
                    # Task hasn't started yet
                    return BatchProcessResponse(
                        batch_id=batch_id,
                        status="PENDING",
                        total_reports=0,
                        successful=0,
                        failed=0,
                        results=[],
                        processed_at=datetime.now(timezone.utc).isoformat(),
                        task_id=task_id
                    )
                elif task_state == "PROCESSING":
                    # Task is running, get progress from meta
                    meta = task.info or {}
                    return BatchProcessResponse(
                        batch_id=batch_id,
                        status="PROCESSING",
                        total_reports=meta.get("total_reports", 0),
                        successful=meta.get("successful", 0),
                        failed=meta.get("failed", 0),
                        results=meta.get("results", []),
                        processed_at=datetime.now(timezone.utc).isoformat(),
                        task_id=task_id
                    )
                elif task_state == "SUCCESS":
                    # Task completed successfully
                    result = task.result
                    return BatchProcessResponse(
                        batch_id=batch_id,
                        status=result.get("status", "COMPLETED"),
                        total_reports=result.get("total_reports", 0),
                        successful=result.get("successful", 0),
                        failed=result.get("failed", 0),
                        results=result.get("results", []),
                        processed_at=result.get("processed_at", datetime.now(timezone.utc).isoformat()),
                        task_id=task_id
                    )
                elif task_state == "FAILURE":
                    # Task failed
                    error = task.info or {"error": "Unknown error"}
                    return BatchProcessResponse(
                        batch_id=batch_id,
                        status="FAILED",
                        total_reports=0,
                        successful=0,
                        failed=0,
                        results=[],
                        processed_at=datetime.now(timezone.utc).isoformat(),
                        task_id=task_id
                    )
            except Exception as e:
                logger.warning(f"Failed to get Celery task status: {e}")
        
        # Fallback: Query reports by status (if batch_id tracking is implemented)
        # For now, return a basic response
        # In production, implement BatchJob model to track batch_id -> report_ids mapping
        processor = BatchProcessor(db)
        
        # This is a placeholder - in production, store batch_id with reports
        return BatchProcessResponse(
            batch_id=batch_id,
            status="PROCESSING",
            total_reports=0,
            successful=0,
            failed=0,
            results=[],
            processed_at=datetime.now(timezone.utc).isoformat(),
            task_id=task_id
        )
        
    except Exception as e:
        logger.error(f"Error getting batch status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch status: {str(e)}"
        )


@router.patch("/{report_id}/status", response_model=ReportResponse)
async def update_report_status(
    report_id: str,
    payload: UpdateReportStatusRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the processing status of a financial report.

    Allows marking a report back to PENDING to re-queue processing or for manual correction.
    """
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report ID format")

    report: FinancialReport | None = db.query(FinancialReport).filter(FinancialReport.id == report_uuid).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Update status
    new_status = ProcessingStatus(payload.status)
    report.processing_status = new_status
    # If moving to PENDING, clear processed_at so UI reflects pending state consistently
    if new_status == ProcessingStatus.PENDING:
        report.processed_at = None

    report.updated_at = datetime.now(timezone.utc)
    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportResponse(
        id=str(report.id),
        company_id=str(report.company_id),
        company_name=report.company.company_name if report.company else None,
        ticker_symbol=report.company.ticker_symbol if report.company else None,
        report_type=report.report_type.value if report.report_type else "Other",
        fiscal_period=report.fiscal_period,
        filing_date=report.filing_date.isoformat() if report.filing_date else None,
        file_format=report.file_format.value if report.file_format else "TXT",
        file_size_bytes=report.file_size_bytes,
        download_source=report.download_source.value if report.download_source else "MANUAL_UPLOAD",
        processing_status=report.processing_status.value if report.processing_status else "PENDING",
        created_at=report.created_at.isoformat() if report.created_at else datetime.now(timezone.utc).isoformat(),
        processed_at=report.processed_at.isoformat() if report.processed_at else None,
    )

