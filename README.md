# MergerTracker - M&A News Scraping WebApp

A comprehensive webapp for scraping merger and acquisition news from multiple financial sources, extracting key deal information, and providing AI-powered summaries.

## 🎯 Project Overview

MergerTracker aggregates M&A news from major financial sources (Reuters, Bloomberg, WSJ, Financial Times) on a daily basis, extracts structured deal information using AI/ML techniques, and provides real-time access through modern APIs and a responsive web interface.

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI with Python 3.11+
- **Database**: PostgreSQL with TimescaleDB extension
- **Scraping**: Scrapy + Playwright for dynamic content
- **AI/ML**: Claude 4 Sonnet API for summarization
- **Frontend**: React 18+ with TypeScript
- **Caching**: Redis
- **Scheduling**: APScheduler

### Key Features
- Daily automated news scraping from 20+ financial sources
- AI-powered news summarization and information extraction
- Structured M&A deal database with time-series optimization
- RESTful API with GraphQL for complex queries
- Real-time updates and market analytics
- Comprehensive legal compliance framework

## 📁 Project Structure

```
MergerTracker/
├── backend/                 # FastAPI backend services
│   ├── api/                # API endpoints and routes
│   ├── scraper/            # Scrapy spiders and scraping logic
│   ├── models/             # SQLAlchemy database models
│   ├── services/           # Business logic and AI integration
│   └── config/             # Configuration files
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client services
│   │   └── utils/          # Utility functions
│   └── public/             # Static assets
├── database/               # Database schemas and migrations
│   ├── migrations/         # SQLAlchemy migrations
│   └── scripts/            # Database setup scripts
├── docs/                   # Project documentation
├── infrastructure/         # Docker, Kubernetes configs
├── tests/                  # Test suites
└── deployment/            # Deployment scripts and configs
```

## 🚀 Development Phases

### Phase 1: Foundation (Weeks 1-4)
- Infrastructure setup with Docker
- Database design and FastAPI application structure
- Authentication and basic security

### Phase 2: Core Scraping (Weeks 5-8)
- Scrapy spiders for major news sources
- Data validation and cleaning pipelines
- Rate limiting and error handling

### Phase 3: AI Integration (Weeks 9-12)
- Claude API integration for summarization
- Structured data extraction and NER
- Deal matching algorithms

### Phase 4: API Development (Weeks 13-16)
- REST API endpoints with filtering and search
- GraphQL for complex queries
- Real-time updates with WebSockets

### Phase 5: Frontend Development (Weeks 17-20)
- React application with TypeScript
- Deal dashboard and news feed
- Data visualization components

### Phase 6: Testing & Deployment (Weeks 21-24)
- Comprehensive testing and security assessment
- Production deployment and CI/CD setup
- Performance optimization

## 📊 Key Data Fields

### Deal Information
- Deal ID, announcement/completion dates
- Deal type, value, and payment method
- Deal status and enterprise value

### Company Information
- Company names, ticker symbols
- Industry classification (SIC codes)
- Employee count and website domains

### Financial Metrics
- Purchase price multiples
- Revenue and EBITDA multiples
- Stock premium percentages

## 🛡️ Legal Compliance

- Respectful scraping with rate limiting (1-5s delays)
- Terms of Service compliance review
- GDPR/CCPA data protection measures
- PII filtering and data retention policies

## 📈 Success Metrics

- **Performance**: 95% daily scraping success rate, <500ms API response time
- **Quality**: 90% data accuracy rate, high AI summary quality scores
- **Reliability**: 99.5% system uptime

## 🔧 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ with TimescaleDB
- Redis
- Node.js 18+ (for frontend)

### Quick Start
```bash
# Clone and setup
git clone git@github.com:Donkey1996/MergerTracker.git
cd MergerTracker

# Backend setup
cd backend
pip install -r requirements.txt
alembic upgrade head

# Frontend setup
cd ../frontend
npm install
npm start

# Start services
docker-compose up -d
```

## 📖 Documentation

- [Comprehensive Research Report](./comprehensive_research_report.md)
- [API Documentation](./docs/api.md)
- [Database Schema](./docs/database.md)
- [Deployment Guide](./docs/deployment.md)

## 🤝 Contributing

Please read our [Contributing Guide](./docs/contributing.md) for development practices and code standards.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.