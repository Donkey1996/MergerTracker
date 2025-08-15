from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from typing import List, Optional
from datetime import datetime, date
import structlog

from config.database import get_db
from models.deals import Deal, DealParticipant, DealStatus, DealType
from models.companies import Company
from services.deals import DealService
from api.schemas.deals import DealResponse, DealCreate, DealUpdate, DealListResponse

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=DealListResponse)
async def get_deals(
    skip: int = Query(0, ge=0, description="Number of deals to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of deals to return"),
    status: Optional[DealStatus] = Query(None, description="Filter by deal status"),
    deal_type: Optional[DealType] = Query(None, description="Filter by deal type"),
    min_value: Optional[float] = Query(None, ge=0, description="Minimum deal value in millions"),
    max_value: Optional[float] = Query(None, ge=0, description="Maximum deal value in millions"),
    start_date: Optional[date] = Query(None, description="Filter deals announced after this date"),
    end_date: Optional[date] = Query(None, description="Filter deals announced before this date"),
    search: Optional[str] = Query(None, description="Search in deal headlines and descriptions"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of M&A deals with filtering and pagination"""
    try:
        deal_service = DealService(db)
        
        filters = {}
        if status:
            filters['status'] = status
        if deal_type:
            filters['deal_type'] = deal_type
        if min_value is not None:
            filters['min_value'] = min_value
        if max_value is not None:
            filters['max_value'] = max_value
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if search:
            filters['search'] = search
            
        deals, total = await deal_service.get_deals(
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        return DealListResponse(
            deals=[deal.to_dict() for deal in deals],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error("Failed to get deals", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve deals")


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific deal by ID"""
    try:
        deal_service = DealService(db)
        deal = await deal_service.get_deal_by_id(deal_id)
        
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
            
        return DealResponse(**deal.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get deal", deal_id=deal_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve deal")


@router.post("/", response_model=DealResponse, status_code=201)
async def create_deal(
    deal_data: DealCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new M&A deal"""
    try:
        deal_service = DealService(db)
        deal = await deal_service.create_deal(deal_data.dict())
        
        logger.info("Deal created", deal_id=str(deal.deal_id))
        return DealResponse(**deal.to_dict())
        
    except Exception as e:
        logger.error("Failed to create deal", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create deal")


@router.put("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: str,
    deal_data: DealUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update existing deal"""
    try:
        deal_service = DealService(db)
        deal = await deal_service.update_deal(deal_id, deal_data.dict(exclude_unset=True))
        
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
            
        logger.info("Deal updated", deal_id=deal_id)
        return DealResponse(**deal.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update deal", deal_id=deal_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update deal")


@router.delete("/{deal_id}", status_code=204)
async def delete_deal(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete deal"""
    try:
        deal_service = DealService(db)
        success = await deal_service.delete_deal(deal_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Deal not found")
            
        logger.info("Deal deleted", deal_id=deal_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete deal", deal_id=deal_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete deal")


@router.get("/{deal_id}/news")
async def get_deal_news(
    deal_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Get news articles related to a specific deal"""
    try:
        deal_service = DealService(db)
        deal = await deal_service.get_deal_by_id(deal_id)
        
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
            
        news_articles = await deal_service.get_deal_news(deal_id, skip, limit)
        
        return {
            "articles": [article.to_summary_dict() for article in news_articles],
            "deal_id": deal_id,
            "total": len(news_articles)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get deal news", deal_id=deal_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve deal news")


@router.get("/{deal_id}/participants")
async def get_deal_participants(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get participants (target/acquirer companies) for a deal"""
    try:
        deal_service = DealService(db)
        deal = await deal_service.get_deal_by_id(deal_id)
        
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
            
        participants = await deal_service.get_deal_participants(deal_id)
        
        return {
            "participants": [participant.to_dict() for participant in participants],
            "deal_id": deal_id,
            "total": len(participants)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get deal participants", deal_id=deal_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve deal participants")