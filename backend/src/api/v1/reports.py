"""Financial report endpoints for FNA backend API."""

import os
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from ...core.security import get_current_user, require_pro_tier
from ...database.connection import get_db
from ...models.company import Company
from ...models.financial_report import FinancialReport, ReportType, FileFormat, ProcessingStatus, DownloadSource
from ...services.document_processor import DocumentProcessor

router = APIRouter()

# Constants and configuration
UPLOAD_DIR = Path("uploads/reports")
ALLOWED_MIME_TYPES = {
    "application/pdf": FileFormat.PDF,
    "text/html": FileFormat.HTML,
    "application/xhtml+xml": FileFormat.HTML,
    "text/plain": FileFormat.TXT,
    "application/xml": FileFormat.iXBRL,
    "text/xml": FileFormat.iXBRL
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
    """Background task to process uploaded report."""
    try:
        # This would typically be handled by a task queue (Celery, etc.)
        # For now, we'll use a simple background task
        processor = DocumentProcessor()
        # await processor.process_report(report_id)  # This would be implemented
        pass
    except Exception as e:
        # Log error and update report status
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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List financial reports with optional filtering.
    
    TODO: Replace with database query with proper filtering.
    """
    # Mock reports for development
    mock_reports = [
        {
            "id": "report-1",
            "company_id": "company-1", 
            "report_type": "10-K",
            "fiscal_period": "FY 2024",
            "filing_date": "2024-10-31",
            "file_format": "HTML",
            "processing_status": "COMPLETED",
            "created_at": "2025-10-29T00:00:00"
        },
        {
            "id": "report-2",
            "company_id": "company-1",
            "report_type": "10-Q", 
            "fiscal_period": "Q3 2024",
            "filing_date": "2024-07-31",
            "file_format": "iXBRL",
            "processing_status": "PROCESSING",
            "created_at": "2025-10-29T01:00:00"
        }
    ]
    
    # Apply mock filtering
    filtered_reports = mock_reports
    if company_id:
        filtered_reports = [r for r in filtered_reports if r["company_id"] == company_id]
    if report_type:
        filtered_reports = [r for r in filtered_reports if r["report_type"] == report_type] 
    if status:
        filtered_reports = [r for r in filtered_reports if r["processing_status"] == status]
    
    return filtered_reports[skip:skip + limit]


@router.post("/upload", response_model=ReportUploadResponse)
async def upload_report(
    background_tasks: BackgroundTasks,
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
        
        # Queue background processing
        background_tasks.add_task(process_report_background, str(new_report.id))
        
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
        # Auto-create company with basic info
        company = Company(
            id=uuid.uuid4(),
            ticker_symbol=download_request.ticker_symbol,
            company_name=f"{download_request.ticker_symbol} Corporation",  # Placeholder name
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
        
        # Ensure upload directory exists
        ensure_upload_directory()
        
        # Generate file path for downloaded report
        original_filename = download_result['filename']
        file_path = generate_file_path(str(company.id), original_filename)
        
        # Move downloaded file to organized location
        downloaded_file_path = Path(download_result['file_path'])
        shutil.move(str(downloaded_file_path), str(file_path))
        
        # Create database record
        new_report = FinancialReport(
            id=uuid.uuid4(),
            company_id=company.id,
            report_type=ReportType(download_request.report_type),
            fiscal_period=download_result.get('fiscal_period'),
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
        
        # Queue background processing
        background_tasks.add_task(process_report_background, str(new_report.id))
        
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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed information about a specific report.
    
    TODO: Replace with database query.
    """
    # Mock report lookup
    if not report_id.startswith("report-"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    mock_report = {
        "id": report_id,
        "company_id": "company-1",
        "report_type": "10-K",
        "fiscal_period": "FY 2024", 
        "filing_date": "2024-10-31",
        "file_format": "HTML",
        "processing_status": "COMPLETED",
        "created_at": "2025-10-29T00:00:00"
    }
    
    return ReportResponse(**mock_report)


class AnalysisResponse(BaseModel):
    """Narrative analysis response model."""
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
