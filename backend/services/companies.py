from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple, Dict, Any
import structlog
from uuid import UUID

from models.companies import Company
from models.deals import Deal, DealParticipant

logger = structlog.get_logger(__name__)


class CompanyService:
    """Service class for company-related operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_companies(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Company], int]:
        """Get companies with filtering and pagination"""
        try:
            # Base query
            query = select(Company)
            count_query = select(func.count(Company.company_id))
            
            # Apply filters
            if filters:
                conditions = []
                
                if 'search' in filters:
                    search_term = f"%{filters['search']}%"
                    conditions.append(
                        Company.company_name.ilike(search_term)
                    )
                
                if 'industry' in filters:
                    conditions.append(
                        Company.industry_sic_code == filters['industry']
                    )
                
                if conditions:
                    query = query.where(and_(*conditions))
                    count_query = count_query.where(and_(*conditions))
            
            # Order by company name
            query = query.order_by(Company.company_name)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute queries
            result = await self.db.execute(query)
            companies = result.scalars().all()
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            return companies, total
            
        except Exception as e:
            logger.error("Failed to get companies", error=str(e))
            raise
    
    async def get_company_by_id(self, company_id: str) -> Optional[Company]:
        """Get company by ID"""
        try:
            query = select(Company).where(Company.company_id == UUID(company_id))
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get company by ID", company_id=company_id, error=str(e))
            raise
    
    async def get_company_deals(
        self,
        company_id: str,
        skip: int = 0,
        limit: int = 50,
        role: Optional[str] = None
    ) -> List[Deal]:
        """Get deals where company participated as target or acquirer"""
        try:
            # Base query for deals through participants
            query = select(Deal).join(DealParticipant).options(
                selectinload(Deal.participants).selectinload(DealParticipant.target_company),
                selectinload(Deal.participants).selectinload(DealParticipant.acquirer_company)
            )
            
            # Filter by role
            conditions = []
            company_uuid = UUID(company_id)
            
            if role == "target":
                conditions.append(DealParticipant.target_company_id == company_uuid)
            elif role == "acquirer":
                conditions.append(DealParticipant.acquirer_company_id == company_uuid)
            else:
                # Both roles
                conditions.append(
                    or_(
                        DealParticipant.target_company_id == company_uuid,
                        DealParticipant.acquirer_company_id == company_uuid
                    )
                )
            
            query = query.where(and_(*conditions))
            query = query.order_by(desc(Deal.announcement_date))
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error("Failed to get company deals", company_id=company_id, error=str(e))
            raise