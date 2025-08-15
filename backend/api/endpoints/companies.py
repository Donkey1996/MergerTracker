from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import structlog

from config.database import get_db
from models.companies import Company
from services.companies import CompanyService

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/")
async def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search company names"),
    industry: Optional[str] = Query(None, description="Filter by industry SIC code"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of companies with filtering and pagination"""
    try:
        company_service = CompanyService(db)
        
        filters = {}
        if search:
            filters['search'] = search
        if industry:
            filters['industry'] = industry
            
        companies, total = await company_service.get_companies(
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        return {
            "companies": [company.to_dict() for company in companies],
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error("Failed to get companies", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve companies")


@router.get("/{company_id}")
async def get_company(
    company_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific company by ID"""
    try:
        company_service = CompanyService(db)
        company = await company_service.get_company_by_id(company_id)
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        return company.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get company", company_id=company_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve company")


@router.get("/{company_id}/deals")
async def get_company_deals(
    company_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    role: Optional[str] = Query(None, description="Filter by role: target, acquirer, or both"),
    db: AsyncSession = Depends(get_db)
):
    """Get deals where company was involved as target or acquirer"""
    try:
        company_service = CompanyService(db)
        company = await company_service.get_company_by_id(company_id)
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        deals = await company_service.get_company_deals(
            company_id, skip, limit, role
        )
        
        return {
            "deals": [deal.to_dict() for deal in deals],
            "company_id": company_id,
            "company_name": company.company_name,
            "total": len(deals)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get company deals", company_id=company_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve company deals")