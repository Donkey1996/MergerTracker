from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, text
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, date
import structlog
from uuid import UUID

from models.deals import Deal, DealParticipant, DealStatus, DealType
from models.companies import Company
from models.news import NewsArticle

logger = structlog.get_logger(__name__)


class DealService:
    """Service class for deal-related operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_deals(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Deal], int]:
        """Get deals with filtering and pagination"""
        try:
            # Base query with relationships
            query = select(Deal).options(
                selectinload(Deal.participants).selectinload(DealParticipant.target_company),
                selectinload(Deal.participants).selectinload(DealParticipant.acquirer_company)
            )
            
            # Count query for total
            count_query = select(func.count(Deal.deal_id))
            
            # Apply filters
            if filters:
                conditions = []
                
                if 'status' in filters:
                    conditions.append(Deal.deal_status == filters['status'])
                
                if 'deal_type' in filters:
                    conditions.append(Deal.deal_type == filters['deal_type'])
                
                if 'min_value' in filters:
                    conditions.append(Deal.deal_value >= filters['min_value'])
                
                if 'max_value' in filters:
                    conditions.append(Deal.deal_value <= filters['max_value'])
                
                if 'start_date' in filters:
                    conditions.append(Deal.announcement_date >= filters['start_date'])
                
                if 'end_date' in filters:
                    conditions.append(Deal.announcement_date <= filters['end_date'])
                
                if 'search' in filters:
                    search_term = f"%{filters['search']}%"
                    conditions.append(
                        or_(
                            Deal.deal_headline.ilike(search_term),
                            Deal.deal_description.ilike(search_term)
                        )
                    )
                
                if conditions:
                    query = query.where(and_(*conditions))
                    count_query = count_query.where(and_(*conditions))
            
            # Order by announcement date (newest first)
            query = query.order_by(desc(Deal.announcement_date))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute queries
            result = await self.db.execute(query)
            deals = result.scalars().all()
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            return deals, total
            
        except Exception as e:
            logger.error("Failed to get deals", error=str(e))
            raise
    
    async def get_deal_by_id(self, deal_id: str) -> Optional[Deal]:
        """Get deal by ID with all relationships"""
        try:
            query = select(Deal).options(
                selectinload(Deal.participants).selectinload(DealParticipant.target_company),
                selectinload(Deal.participants).selectinload(DealParticipant.acquirer_company),
                selectinload(Deal.news_articles)
            ).where(Deal.deal_id == UUID(deal_id))
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get deal by ID", deal_id=deal_id, error=str(e))
            raise
    
    async def create_deal(self, deal_data: Dict[str, Any]) -> Deal:
        """Create new deal"""
        try:
            # Create deal instance
            deal = Deal(**deal_data)
            self.db.add(deal)
            await self.db.flush()  # Get the ID without committing
            
            await self.db.refresh(deal)
            await self.db.commit()
            
            logger.info("Deal created successfully", deal_id=str(deal.deal_id))
            return deal
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to create deal", error=str(e))
            raise
    
    async def update_deal(self, deal_id: str, deal_data: Dict[str, Any]) -> Optional[Deal]:
        """Update existing deal"""
        try:
            query = select(Deal).where(Deal.deal_id == UUID(deal_id))
            result = await self.db.execute(query)
            deal = result.scalar_one_or_none()
            
            if not deal:
                return None
            
            # Update fields
            for field, value in deal_data.items():
                if hasattr(deal, field) and value is not None:
                    setattr(deal, field, value)
            
            await self.db.commit()
            await self.db.refresh(deal)
            
            logger.info("Deal updated successfully", deal_id=deal_id)
            return deal
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to update deal", deal_id=deal_id, error=str(e))
            raise
    
    async def delete_deal(self, deal_id: str) -> bool:
        """Delete deal"""
        try:
            query = select(Deal).where(Deal.deal_id == UUID(deal_id))
            result = await self.db.execute(query)
            deal = result.scalar_one_or_none()
            
            if not deal:
                return False
            
            await self.db.delete(deal)
            await self.db.commit()
            
            logger.info("Deal deleted successfully", deal_id=deal_id)
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to delete deal", deal_id=deal_id, error=str(e))
            raise
    
    async def get_deal_news(
        self,
        deal_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[NewsArticle]:
        """Get news articles for a specific deal"""
        try:
            query = select(NewsArticle).where(
                NewsArticle.deal_id == UUID(deal_id)
            ).order_by(desc(NewsArticle.publish_date)).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error("Failed to get deal news", deal_id=deal_id, error=str(e))
            raise
    
    async def get_deal_participants(self, deal_id: str) -> List[DealParticipant]:
        """Get participants for a specific deal"""
        try:
            query = select(DealParticipant).options(
                selectinload(DealParticipant.target_company),
                selectinload(DealParticipant.acquirer_company)
            ).where(DealParticipant.deal_id == UUID(deal_id))
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error("Failed to get deal participants", deal_id=deal_id, error=str(e))
            raise
    
    async def get_deals_analytics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get deal analytics and statistics"""
        try:
            base_query = select(Deal)
            
            # Apply date filters
            conditions = []
            if start_date:
                conditions.append(Deal.announcement_date >= start_date)
            if end_date:
                conditions.append(Deal.announcement_date <= end_date)
            
            if conditions:
                base_query = base_query.where(and_(*conditions))
            
            # Total deals
            count_query = select(func.count(Deal.deal_id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            count_result = await self.db.execute(count_query)
            total_deals = count_result.scalar()
            
            # Total and average deal value
            value_query = select(
                func.sum(Deal.deal_value),
                func.avg(Deal.deal_value)
            ).where(Deal.deal_value.is_not(None))
            
            if conditions:
                value_query = value_query.where(and_(*conditions))
            
            value_result = await self.db.execute(value_query)
            total_value, avg_value = value_result.one()
            
            # Deals by status
            status_query = select(
                Deal.deal_status,
                func.count(Deal.deal_id)
            ).group_by(Deal.deal_status)
            
            if conditions:
                status_query = status_query.where(and_(*conditions))
            
            status_result = await self.db.execute(status_query)
            deals_by_status = {row[0].value: row[1] for row in status_result.all()}
            
            # Deals by type
            type_query = select(
                Deal.deal_type,
                func.count(Deal.deal_id)
            ).group_by(Deal.deal_type)
            
            if conditions:
                type_query = type_query.where(and_(*conditions))
            
            type_result = await self.db.execute(type_query)
            deals_by_type = {row[0].value: row[1] for row in type_result.all()}
            
            # Monthly deal trends
            monthly_query = select(
                func.date_trunc('month', Deal.announcement_date).label('month'),
                func.count(Deal.deal_id).label('count'),
                func.sum(Deal.deal_value).label('total_value')
            ).group_by('month').order_by('month')
            
            if conditions:
                monthly_query = monthly_query.where(and_(*conditions))
            
            monthly_result = await self.db.execute(monthly_query)
            deals_by_month = {
                row.month.strftime('%Y-%m'): {
                    'count': row.count,
                    'total_value': float(row.total_value) if row.total_value else 0
                }
                for row in monthly_result.all()
            }
            
            return {
                'total_deals': total_deals,
                'total_value': float(total_value) if total_value else None,
                'average_deal_value': float(avg_value) if avg_value else None,
                'deals_by_status': deals_by_status,
                'deals_by_type': deals_by_type,
                'deals_by_month': deals_by_month
            }
            
        except Exception as e:
            logger.error("Failed to get deals analytics", error=str(e))
            raise