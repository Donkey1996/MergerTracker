from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from models.deals import DealStatus, DealType, PaymentMethod


class CompanyBasic(BaseModel):
    """Basic company information for deal responses"""
    company_id: str
    company_name: str
    ticker_symbol: Optional[str] = None
    industry_sic_code: Optional[str] = None


class DealParticipantResponse(BaseModel):
    """Deal participant response model"""
    participant_id: str
    target_company: Optional[CompanyBasic] = None
    acquirer_company: Optional[CompanyBasic] = None
    ownership_percentage: Optional[float] = None
    participation_type: str


class DealBase(BaseModel):
    """Base deal model with common fields"""
    announcement_date: datetime
    completion_date: Optional[datetime] = None
    deal_status: DealStatus
    deal_type: DealType
    deal_value: Optional[float] = Field(None, description="Deal value in millions USD")
    enterprise_value: Optional[float] = Field(None, description="Enterprise value in millions USD")
    payment_method: Optional[PaymentMethod] = None
    deal_headline: Optional[str] = None
    deal_description: Optional[str] = None
    deal_rationale: Optional[str] = None


class DealCreate(DealBase):
    """Schema for creating new deals"""
    # Required fields for creation
    announcement_date: datetime
    deal_status: DealStatus = DealStatus.ANNOUNCED
    deal_type: DealType
    
    # Optional fields
    purchase_price_multiple: Optional[float] = None
    revenue_multiple: Optional[float] = None
    ebitda_multiple: Optional[float] = None
    stock_premium_percentage: Optional[float] = None
    financial_advisors: Optional[str] = None
    legal_advisors: Optional[str] = None
    advisory_fees: Optional[float] = None
    regulatory_approvals_required: Optional[str] = None
    approval_status: Optional[str] = None
    
    @validator('deal_value', 'enterprise_value', 'advisory_fees')
    def validate_positive_values(cls, v):
        if v is not None and v < 0:
            raise ValueError('Financial values must be positive')
        return v
    
    @validator('stock_premium_percentage')
    def validate_percentage(cls, v):
        if v is not None and (v < -100 or v > 1000):
            raise ValueError('Stock premium percentage must be between -100% and 1000%')
        return v


class DealUpdate(BaseModel):
    """Schema for updating existing deals"""
    announcement_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    deal_status: Optional[DealStatus] = None
    deal_type: Optional[DealType] = None
    deal_value: Optional[float] = None
    enterprise_value: Optional[float] = None
    payment_method: Optional[PaymentMethod] = None
    deal_headline: Optional[str] = None
    deal_description: Optional[str] = None
    deal_rationale: Optional[str] = None
    purchase_price_multiple: Optional[float] = None
    revenue_multiple: Optional[float] = None
    ebitda_multiple: Optional[float] = None
    stock_premium_percentage: Optional[float] = None
    financial_advisors: Optional[str] = None
    legal_advisors: Optional[str] = None
    advisory_fees: Optional[float] = None
    regulatory_approvals_required: Optional[str] = None
    approval_status: Optional[str] = None
    
    @validator('deal_value', 'enterprise_value', 'advisory_fees')
    def validate_positive_values(cls, v):
        if v is not None and v < 0:
            raise ValueError('Financial values must be positive')
        return v


class DealResponse(DealBase):
    """Schema for deal API responses"""
    deal_id: str
    purchase_price_multiple: Optional[float] = None
    revenue_multiple: Optional[float] = None
    ebitda_multiple: Optional[float] = None
    stock_premium_percentage: Optional[float] = None
    financial_advisors: Optional[str] = None
    legal_advisors: Optional[str] = None
    advisory_fees: Optional[float] = None
    regulatory_approvals_required: Optional[str] = None
    approval_status: Optional[str] = None
    source_confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    participants: List[DealParticipantResponse] = []
    
    class Config:
        from_attributes = True


class DealSummary(BaseModel):
    """Summary deal model for list views"""
    deal_id: str
    announcement_date: datetime
    deal_status: DealStatus
    deal_type: DealType
    deal_value: Optional[float] = None
    deal_headline: Optional[str] = None
    target_company: Optional[str] = None
    acquirer_company: Optional[str] = None


class DealListResponse(BaseModel):
    """Response for deal list endpoints"""
    deals: List[dict]
    total: int
    skip: int
    limit: int
    
    
class DealSearchFilters(BaseModel):
    """Advanced search filters for deals"""
    status: Optional[List[DealStatus]] = None
    deal_types: Optional[List[DealType]] = None
    min_value: Optional[float] = Field(None, ge=0)
    max_value: Optional[float] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    industries: Optional[List[str]] = None
    companies: Optional[List[str]] = None
    search_terms: Optional[str] = None
    
    
class DealAnalytics(BaseModel):
    """Deal analytics response"""
    total_deals: int
    total_value: Optional[float] = None
    average_deal_value: Optional[float] = None
    deals_by_status: dict
    deals_by_type: dict
    deals_by_month: dict
    top_industries: List[dict]
    top_acquirers: List[dict]