"""Company endpoints for FNA backend API."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from ...core.security import get_current_user

router = APIRouter()


# Request/Response models
class CompanyResponse(BaseModel):
    """Company information response model."""
    id: str
    ticker_symbol: str
    company_name: str
    sector: str
    industry: str
    created_at: str


class CompanyCreateRequest(BaseModel):
    """Company creation request model."""
    ticker_symbol: str
    company_name: str
    sector: str = None
    industry: str = None


@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all companies available for analysis.
    
    TODO: Replace with database query.
    """
    # Mock companies for development
    mock_companies = [
        {
            "id": "company-1",
            "ticker_symbol": "AAPL",
            "company_name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "created_at": "2025-10-29T00:00:00"
        },
        {
            "id": "company-2", 
            "ticker_symbol": "MSFT",
            "company_name": "Microsoft Corporation",
            "sector": "Technology",
            "industry": "Software",
            "created_at": "2025-10-29T00:00:00"
        },
        {
            "id": "company-3",
            "ticker_symbol": "TSLA", 
            "company_name": "Tesla, Inc.",
            "sector": "Consumer Cyclical",
            "industry": "Auto Manufacturers",
            "created_at": "2025-10-29T00:00:00"
        }
    ]
    
    return mock_companies[skip:skip + limit]


@router.post("/", response_model=CompanyResponse)
async def add_company(
    company_data: CompanyCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add a new company for analysis.
    
    TODO: Replace with database insertion and validation.
    """
    # Mock company creation
    new_company = {
        "id": f"company-{company_data.ticker_symbol.lower()}",
        "ticker_symbol": company_data.ticker_symbol.upper(),
        "company_name": company_data.company_name,
        "sector": company_data.sector,
        "industry": company_data.industry,
        "created_at": "2025-10-29T00:00:00"
    }
    
    return CompanyResponse(**new_company)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed information about a specific company.
    
    TODO: Replace with database query.
    """
    # Mock company lookup
    if company_id not in ["company-1", "company-2", "company-3"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    mock_company = {
        "id": company_id,
        "ticker_symbol": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology", 
        "industry": "Consumer Electronics",
        "created_at": "2025-10-29T00:00:00"
    }
    
    return CompanyResponse(**mock_company)


@router.get("/{company_id}/reports")
async def get_company_reports(
    company_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all financial reports for a specific company.
    
    TODO: Replace with database query joining companies and financial_reports.
    """
    # Mock reports for company
    mock_reports = [
        {
            "id": "report-1",
            "report_type": "10-K", 
            "fiscal_period": "FY 2024",
            "filing_date": "2024-10-31",
            "processing_status": "COMPLETED"
        },
        {
            "id": "report-2",
            "report_type": "10-Q",
            "fiscal_period": "Q3 2024", 
            "filing_date": "2024-07-31",
            "processing_status": "COMPLETED"
        }
    ]
    
    return mock_reports
