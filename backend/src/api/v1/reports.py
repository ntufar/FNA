"""Financial report endpoints for FNA backend API."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from pydantic import BaseModel

from ...core.security import get_current_user, require_pro_tier

router = APIRouter()


# Request/Response models
class ReportResponse(BaseModel):
    """Financial report response model."""
    id: str
    company_id: str
    report_type: str
    fiscal_period: str
    filing_date: str
    file_format: str
    processing_status: str
    created_at: str


class ReportUploadResponse(BaseModel):
    """Report upload response model."""
    report_id: str
    message: str
    processing_status: str


class SECDownloadRequest(BaseModel):
    """SEC.gov automatic download request."""
    ticker_symbol: str
    report_type: str = "10-K"
    fiscal_year: int = None


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
    company_id: str,
    report_type: str,
    fiscal_period: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Upload a financial report file for analysis.
    
    TODO: Implement file validation, storage, and processing queue.
    """
    # Validate file type
    allowed_types = ["application/pdf", "text/html", "text/plain", "application/xml"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    # Validate file size (50MB limit)
    max_size = 50 * 1024 * 1024  # 50MB in bytes
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 50MB limit"
        )
    
    # TODO: Save file to storage and create database record
    # TODO: Queue for processing with LLM
    
    # Mock response
    report_id = f"report-upload-{len(file_content)}"
    
    return ReportUploadResponse(
        report_id=report_id,
        message="File uploaded successfully and queued for processing",
        processing_status="PENDING"
    )


@router.post("/download", response_model=ReportUploadResponse)
async def download_from_sec(
    download_request: SECDownloadRequest,
    current_user: Dict[str, Any] = Depends(require_pro_tier)
):
    """Automatically download a report from SEC.gov.
    
    Requires Pro or Enterprise subscription.
    TODO: Implement SEC EDGAR API integration.
    """
    # TODO: Implement SEC.gov API integration
    # TODO: Validate ticker symbol exists
    # TODO: Download and store report file
    # TODO: Queue for processing
    
    # Mock response for development
    report_id = f"sec-{download_request.ticker_symbol}-{download_request.report_type}"
    
    return ReportUploadResponse(
        report_id=report_id,
        message=f"SEC report download initiated for {download_request.ticker_symbol}",
        processing_status="PENDING"
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


@router.get("/{report_id}/analysis")
async def get_report_analysis(
    report_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get narrative analysis results for a report.
    
    TODO: Replace with database query joining reports and narrative_analyses.
    """
    # TODO: Check if report exists and analysis is completed
    # TODO: Return analysis results from database
    
    # Mock analysis results
    mock_analysis = {
        "report_id": report_id,
        "optimism_score": 0.65,
        "optimism_confidence": 0.82,
        "risk_score": 0.34,
        "risk_confidence": 0.78,
        "uncertainty_score": 0.28,
        "uncertainty_confidence": 0.85,
        "overall_sentiment_score": 0.67,
        "key_insights": [
            "Strong revenue growth mentioned multiple times",
            "Management confident about market position",
            "Some concerns about supply chain challenges"
        ],
        "analysis_model_version": "qwen-3.4b-2507",
        "created_at": "2025-10-29T02:00:00"
    }
    
    return mock_analysis


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
