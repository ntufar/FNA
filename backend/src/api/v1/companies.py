"""Company endpoints for FNA backend API."""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...core.security import get_current_user
from ...database.connection import get_db
from ...models.company import Company
from ...models.financial_report import FinancialReport

router = APIRouter()


# Request/Response models
class CompanyResponse(BaseModel):
    """Company information response model."""
    id: str
    ticker_symbol: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    reports_count: int = 0
    latest_report_date: Optional[str] = None
    created_at: str


class CompanyCreateRequest(BaseModel):
    """Company creation request model."""
    ticker_symbol: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    
    @validator('ticker_symbol')
    def validate_ticker_symbol(cls, v):
        if not v or len(v) < 1 or len(v) > 5:
            raise ValueError('Ticker symbol must be 1-5 characters')
        # Convert to uppercase and check for valid characters
        v = v.upper()
        if not v.isalnum():
            raise ValueError('Ticker symbol must contain only alphanumeric characters')
        return v
    
    @validator('company_name')
    def validate_company_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Company name must be at least 2 characters')
        return v.strip()


class CompanyListResponse(BaseModel):
    """Response model for company list endpoints."""
    companies: List[CompanyResponse]
    total: int
    page: int
    per_page: int


@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = Query(0, ge=0, description="Number of companies to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of companies to return"),
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List companies available for analysis with optional filtering."""
    
    # Build query with optional filters
    query = db.query(Company)
    
    if ticker:
        query = query.filter(Company.ticker_symbol.ilike(f"%{ticker.upper()}%"))
    
    if sector:
        query = query.filter(Company.sector.ilike(f"%{sector}%"))
    
    # Get total count for pagination info
    total = query.count()
    
    # Apply pagination and get results
    companies = query.offset(skip).limit(limit).all()
    
    # Convert to response format
    company_responses = []
    for company in companies:
        # Get latest report date
        latest_report_date = None
        if company.latest_report:
            latest_report_date = company.latest_report.filing_date.isoformat()
        
        company_responses.append(CompanyResponse(
            id=str(company.id),
            ticker_symbol=company.ticker_symbol,
            company_name=company.company_name,
            sector=company.sector,
            industry=company.industry,
            reports_count=company.reports_count,
            latest_report_date=latest_report_date,
            created_at=company.created_at.isoformat()
        ))
    
    return company_responses


@router.post("/", response_model=CompanyResponse)
async def add_company(
    company_data: CompanyCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new company for analysis and tracking."""
    
    # Check if company with this ticker already exists
    existing_company = db.query(Company).filter(
        Company.ticker_symbol == company_data.ticker_symbol.upper()
    ).first()
    
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with ticker symbol '{company_data.ticker_symbol}' already exists"
        )
    
    # Create new company
    new_company = Company(
        id=uuid.uuid4(),
        ticker_symbol=company_data.ticker_symbol.upper(),
        company_name=company_data.company_name,
        sector=company_data.sector,
        industry=company_data.industry,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    try:
        db.add(new_company)
        db.commit()
        db.refresh(new_company)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company"
        )
    
    return CompanyResponse(
        id=str(new_company.id),
        ticker_symbol=new_company.ticker_symbol,
        company_name=new_company.company_name,
        sector=new_company.sector,
        industry=new_company.industry,
        reports_count=0,
        latest_report_date=None,
        created_at=new_company.created_at.isoformat()
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific company."""
    
    try:
        # Convert company_id to UUID format for database lookup
        company_uuid = uuid.UUID(company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid company ID format"
        )
    
    # Query company from database
    company = db.query(Company).filter(Company.id == company_uuid).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Get latest report date
    latest_report_date = None
    if company.latest_report:
        latest_report_date = company.latest_report.filing_date.isoformat()
    
    return CompanyResponse(
        id=str(company.id),
        ticker_symbol=company.ticker_symbol,
        company_name=company.company_name,
        sector=company.sector,
        industry=company.industry,
        reports_count=company.reports_count,
        latest_report_date=latest_report_date,
        created_at=company.created_at.isoformat()
    )


@router.get("/{company_id}/reports")
async def get_company_reports(
    company_id: str,
    skip: int = Query(0, ge=0, description="Number of reports to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of reports to return"),
    report_type: Optional[str] = Query(None, description="Filter by report type (10-K, 10-Q, 8-K)"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all financial reports for a specific company."""
    
    try:
        # Convert company_id to UUID format
        company_uuid = uuid.UUID(company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid company ID format"
        )
    
    # Verify company exists
    company = db.query(Company).filter(Company.id == company_uuid).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Build query for financial reports
    query = db.query(FinancialReport).filter(FinancialReport.company_id == company_uuid)
    
    if report_type:
        query = query.filter(FinancialReport.report_type == report_type.upper())
    
    # Order by filing date (most recent first)
    query = query.order_by(FinancialReport.filing_date.desc())
    
    # Apply pagination
    reports = query.offset(skip).limit(limit).all()
    
    # Convert to response format
    report_responses = []
    for report in reports:
        report_responses.append({
            "id": str(report.id),
            "report_type": report.report_type,
            "fiscal_period": report.fiscal_period,
            "filing_date": report.filing_date.isoformat() if report.filing_date else None,
            "file_format": report.file_format,
            "file_size_bytes": report.file_size_bytes,
            "processing_status": report.processing_status,
            "download_source": report.download_source,
            "created_at": report.created_at.isoformat(),
            "processed_at": report.processed_at.isoformat() if report.processed_at else None
        })
    
    return {
        "reports": report_responses,
        "total": len(report_responses),
        "company": {
            "id": str(company.id),
            "ticker_symbol": company.ticker_symbol,
            "company_name": company.company_name
        }
    }
