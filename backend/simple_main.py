#!/usr/bin/env python3
"""
Simplified MergerTracker API for local development
Runs without database or scraping dependencies
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os

app = FastAPI(
    title="MergerTracker API (Simplified)",
    description="M&A News Scraping and Analysis Platform - Development Mode",
    version="1.0.0-dev",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data models
class Deal(BaseModel):
    deal_id: str
    deal_type: str
    target_company: str
    acquirer_company: str
    deal_value: Optional[float] = None
    deal_value_currency: str = "USD"
    industry_sector: str
    deal_status: str
    announcement_date: Optional[str] = None
    created_date: str

class Company(BaseModel):
    company_id: str
    company_name: str
    industry: str
    market_cap: Optional[float] = None
    headquarters: Optional[str] = None

class NewsArticle(BaseModel):
    url: str
    title: str
    source: str
    published_date: str
    summary: Optional[str] = None

# Sample data
sample_deals = [
    Deal(
        deal_id="deal_001",
        deal_type="acquisition",
        target_company="TechCorp Solutions",
        acquirer_company="Global Systems Inc",
        deal_value=1500000000,
        industry_sector="technology",
        deal_status="announced",
        announcement_date="2025-01-15",
        created_date=datetime.utcnow().isoformat()
    ),
    Deal(
        deal_id="deal_002", 
        deal_type="merger",
        target_company="HealthTech Innovations",
        acquirer_company="MedSys Corporation",
        deal_value=850000000,
        industry_sector="healthcare",
        deal_status="pending",
        announcement_date="2025-01-10",
        created_date=datetime.utcnow().isoformat()
    ),
    Deal(
        deal_id="deal_003",
        deal_type="acquisition",
        target_company="FinanceStart",
        acquirer_company="Big Bank Corp",
        deal_value=2200000000,
        industry_sector="finance",
        deal_status="completed",
        announcement_date="2024-12-20",
        created_date=datetime.utcnow().isoformat()
    )
]

sample_companies = [
    Company(
        company_id="comp_001",
        company_name="TechCorp Solutions",
        industry="Software",
        market_cap=5000000000,
        headquarters="San Francisco, CA"
    ),
    Company(
        company_id="comp_002",
        company_name="Global Systems Inc",
        industry="Enterprise Software",
        market_cap=45000000000,
        headquarters="Seattle, WA"
    )
]

sample_articles = [
    NewsArticle(
        url="https://example.com/article1",
        title="TechCorp Solutions Acquired by Global Systems for $1.5B",
        source="TechNews",
        published_date="2025-01-15T10:30:00Z",
        summary="Global Systems Inc announced the acquisition of TechCorp Solutions in a $1.5 billion deal."
    ),
    NewsArticle(
        url="https://example.com/article2", 
        title="HealthTech and MedSys Announce Merger Plans",
        source="HealthBiz",
        published_date="2025-01-10T14:15:00Z",
        summary="Two leading healthcare technology companies plan to merge in an $850 million transaction."
    )
]

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to MergerTracker API (Development Mode)",
        "version": "1.0.0-dev",
        "docs": "/docs",
        "health": "/health",
        "status": "running_simplified_mode"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MergerTracker API (Simplified)",
        "version": "1.0.0-dev",
        "mode": "development",
        "services": {
            "database": {"status": "mocked", "note": "Using sample data"},
            "scheduler": {"status": "disabled", "note": "Simplified mode"}
        }
    }

# Deals endpoints
@app.get("/api/v1/deals", response_model=List[Deal])
async def list_deals(
    limit: int = 100,
    offset: int = 0,
    industry: Optional[str] = None,
    deal_type: Optional[str] = None
):
    """List M&A deals with filtering"""
    filtered_deals = sample_deals
    
    # Apply filters
    if industry:
        filtered_deals = [d for d in filtered_deals if d.industry_sector.lower() == industry.lower()]
    if deal_type:
        filtered_deals = [d for d in filtered_deals if d.deal_type.lower() == deal_type.lower()]
    
    # Apply pagination
    paginated_deals = filtered_deals[offset:offset + limit]
    
    return paginated_deals

@app.get("/api/v1/deals/{deal_id}", response_model=Deal)
async def get_deal(deal_id: str):
    """Get a specific deal by ID"""
    for deal in sample_deals:
        if deal.deal_id == deal_id:
            return deal
    
    return {"error": "Deal not found"}, 404

@app.post("/api/v1/deals", response_model=Deal)
async def create_deal(deal: Deal):
    """Create a new deal"""
    deal.created_date = datetime.utcnow().isoformat()
    sample_deals.append(deal)
    return deal

# Companies endpoints
@app.get("/api/v1/companies", response_model=List[Company])
async def list_companies(limit: int = 100, offset: int = 0):
    """List companies"""
    return sample_companies[offset:offset + limit]

@app.get("/api/v1/companies/{company_id}", response_model=Company)
async def get_company(company_id: str):
    """Get a specific company by ID"""
    for company in sample_companies:
        if company.company_id == company_id:
            return company
    
    return {"error": "Company not found"}, 404

# News endpoints
@app.get("/api/v1/news", response_model=List[NewsArticle])
async def list_news(limit: int = 100, offset: int = 0, source: Optional[str] = None):
    """List news articles"""
    filtered_articles = sample_articles
    
    if source:
        filtered_articles = [a for a in filtered_articles if a.source.lower() == source.lower()]
    
    return filtered_articles[offset:offset + limit]

# Analytics endpoints
@app.get("/api/v1/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary"""
    total_deals = len(sample_deals)
    total_value = sum(d.deal_value or 0 for d in sample_deals)
    avg_deal_size = total_value / total_deals if total_deals > 0 else 0
    
    # Industry breakdown
    industry_stats = {}
    for deal in sample_deals:
        industry = deal.industry_sector
        if industry not in industry_stats:
            industry_stats[industry] = {"count": 0, "total_value": 0}
        industry_stats[industry]["count"] += 1
        industry_stats[industry]["total_value"] += deal.deal_value or 0
    
    # Deal type breakdown
    deal_type_stats = {}
    for deal in sample_deals:
        deal_type = deal.deal_type
        if deal_type not in deal_type_stats:
            deal_type_stats[deal_type] = 0
        deal_type_stats[deal_type] += 1
    
    return {
        "summary": {
            "total_deals": total_deals,
            "total_value": total_value,
            "average_deal_size": avg_deal_size,
            "currency": "USD"
        },
        "industry_breakdown": industry_stats,
        "deal_type_breakdown": deal_type_stats,
        "recent_deals": sample_deals[:5]
    }

# Search endpoints
@app.get("/api/v1/search/deals")
async def search_deals(q: str, limit: int = 50):
    """Search deals by text query"""
    results = []
    query_lower = q.lower()
    
    for deal in sample_deals:
        if (query_lower in deal.target_company.lower() or 
            query_lower in deal.acquirer_company.lower() or
            query_lower in deal.industry_sector.lower()):
            results.append(deal)
    
    return results[:limit]

@app.get("/api/v1/search/companies")
async def search_companies(q: str, limit: int = 50):
    """Search companies by text query"""
    results = []
    query_lower = q.lower()
    
    for company in sample_companies:
        if (query_lower in company.company_name.lower() or 
            query_lower in company.industry.lower()):
            results.append(company)
    
    return results[:limit]

# Development/testing endpoints
@app.get("/api/v1/dev/status")
async def dev_status():
    """Development status endpoint"""
    return {
        "mode": "development",
        "simplified": True,
        "sample_data": {
            "deals_count": len(sample_deals),
            "companies_count": len(sample_companies),
            "articles_count": len(sample_articles)
        },
        "note": "This is a simplified version for development. Full features require database setup."
    }

@app.post("/api/v1/dev/reset")
async def reset_data():
    """Reset sample data"""
    global sample_deals, sample_companies, sample_articles
    
    # Reset to original sample data
    sample_deals = [
        Deal(
            deal_id="deal_001",
            deal_type="acquisition",
            target_company="TechCorp Solutions",
            acquirer_company="Global Systems Inc",
            deal_value=1500000000,
            industry_sector="technology",
            deal_status="announced",
            announcement_date="2025-01-15",
            created_date=datetime.utcnow().isoformat()
        )
    ]
    
    return {"message": "Sample data reset successfully"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting MergerTracker API in simplified mode...")
    print("📊 Using sample data (no database required)")
    print("🌐 API Documentation: http://localhost:8000/docs")
    print("❤️  Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )