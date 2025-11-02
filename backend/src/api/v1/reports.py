"""Financial report endpoints for FNA backend API."""

import os
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, validator, ConfigDict
from sqlalchemy.orm import Session

from ...core.security import get_current_user, require_pro_tier
from ...database.connection import get_db
from ...models.company import Company
from ...models.financial_report import FinancialReport, ReportType, FileFormat, ProcessingStatus, DownloadSource
from ...services.document_processor import DocumentProcessor
from ...services.company_lookup import get_official_name_from_ticker

router = APIRouter()

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


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    company_id: str = None,
    report_type: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 50,
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

    reports = query.offset(skip).limit(limit).all()

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
        
        # First, get filing info to check for duplicates before downloading
        filing_info = sec_downloader.get_latest_filing(
            download_request.ticker_symbol,
            download_request.report_type
        )
        
        if not filing_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {download_request.report_type} filings found for {download_request.ticker_symbol}"
            )
        
        # Check if this report already exists
        # Match on: company_id, report_type, and filing_date
        filing_date = None
        if filing_info.filing_date:
            try:
                # SEC filing dates are in YYYY-MM-DD format
                filing_date = datetime.strptime(filing_info.filing_date, "%Y-%m-%d").date()
            except (ValueError, AttributeError):
                # If parsing fails, log but continue with download
                pass
        
        if filing_date:
            existing_report = db.query(FinancialReport).filter(
                FinancialReport.company_id == company.id,
                FinancialReport.report_type == ReportType(download_request.report_type),
                FinancialReport.filing_date == filing_date
            ).first()
            
            if existing_report:
                # Report already exists, return existing report info
                return ReportUploadResponse(
                    report_id=str(existing_report.id),
                    message=f"Report already exists for {download_request.ticker_symbol} ({download_request.report_type}) filed on {filing_date}",
                    processing_status=existing_report.processing_status.value if existing_report.processing_status else ProcessingStatus.PENDING.value,
                    file_path=str(Path(existing_report.file_path).relative_to(UPLOAD_DIR)) if existing_report.file_path else None,
                    estimated_processing_time=None
                )
        
        # No duplicate found, proceed with download
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


@router.post("/batch", response_model=List[ReportUploadResponse])
async def batch_upload_reports(
    reports_data: List[Dict[str, Any]],
    current_user: Dict[str, Any] = Depends(require_pro_tier)
):
    """Upload multiple reports for batch processing.
    
    Requires Pro or Enterprise subscription with batch limits.
    TODO: Implement batch processing with subscription limits.
    """
    # Check batch limit based on subscription tier
    batch_limits = {
        "Basic": 3,
        "Pro": 7, 
        "Enterprise": 10
    }
    
    user_tier = current_user.get("subscription_tier", "Basic")
    max_batch = batch_limits.get(user_tier, 3)
    
    if len(reports_data) > max_batch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size ({len(reports_data)}) exceeds limit for {user_tier} tier ({max_batch})"
        )
    
    # Mock batch processing
    results = []
    for i, report_data in enumerate(reports_data):
        results.append(ReportUploadResponse(
            report_id=f"batch-report-{i+1}",
            message="Queued for batch processing",
            processing_status="PENDING"
        ))
    
    return results
