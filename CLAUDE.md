# MergerTracker - Claude Code Instructions

## Project Overview
MergerTracker is a comprehensive M&A news scraping webapp that aggregates merger and acquisition news from multiple financial sources, extracts key deal information using AI/ML techniques, and provides structured data access through modern APIs.

## Tech Stack
- **Backend**: FastAPI with Python 3.11+
- **Database**: PostgreSQL with TimescaleDB extension
- **Scraping**: Scrapy + Playwright for dynamic content
- **AI/ML**: Claude 4 Sonnet API for summarization
- **Frontend**: React 18+ with TypeScript
- **Caching**: Redis
- **Scheduling**: APScheduler

## Development Commands

### Setup and Installation
```bash
# Start all services with Docker
docker-compose up -d

# Backend setup (if running manually)
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload

# Frontend setup
cd frontend
npm install
npm start

# Run tests
cd backend && pytest tests/
cd frontend && npm test
```

### Database Operations
```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Reset database (development only)
alembic downgrade base
alembic upgrade head
```

### Code Quality
```bash
# Backend linting and formatting
cd backend
black .
flake8 .
mypy .

# Frontend linting
cd frontend
npm run lint
npm run lint:fix
```

## Project Structure
```
MergerTracker/
├── backend/                 # FastAPI backend services
│   ├── api/                # API endpoints and routes
│   ├── scraper/            # Scrapy spiders and scraping logic
│   ├── models/             # SQLAlchemy database models
│   ├── services/           # Business logic and AI integration
│   └── config/             # Configuration files
├── frontend/               # React frontend application
├── database/               # Database schemas and migrations
├── docs/                   # Project documentation
├── infrastructure/         # Docker, Kubernetes configs
└── tests/                  # Test suites
```

## Key Features in Development

### Phase 1: Foundation (Current)
- [x] Project structure and documentation
- [x] Docker environment setup
- [x] Basic FastAPI application
- [ ] Database models and migrations
- [ ] Authentication system

### Phase 2: Core Scraping (Next)
- [ ] Scrapy spiders for major news sources
- [ ] Data validation and cleaning pipelines
- [ ] Rate limiting and error handling
- [ ] APScheduler for daily scraping

### Phase 3: AI Integration
- [ ] Claude API integration for summarization
- [ ] Structured data extraction and NER
- [ ] Deal matching algorithms
- [ ] Confidence scoring system

## API Endpoints (Planned)
```
GET /api/v1/deals              # List M&A deals with filtering
GET /api/v1/deals/{deal_id}    # Get specific deal details
GET /api/v1/companies/{id}/deals # Company deal history
GET /api/v1/news               # Latest M&A news with summaries
POST /api/v1/search            # Advanced search with filters
GET /api/v1/analytics/trends   # M&A market trends
```

## Database Schema (Core Tables)
- `deals` - M&A deal information (TimescaleDB hypertable)
- `companies` - Company information and details
- `deal_participants` - Deal relationships (target/acquirer)
- `news_articles` - Scraped news articles (TimescaleDB hypertable)
- `deal_advisors` - Financial and legal advisors
- `industry_classifications` - SIC code mappings

## Environment Variables
Key environment variables needed:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `CLAUDE_API_KEY` - Claude API key for AI processing
- `OPENAI_API_KEY` - OpenAI API key (fallback)
- `SECRET_KEY` - Application secret key
- `ENVIRONMENT` - development/staging/production

## Legal and Compliance Notes
- All scraping follows robots.txt and ToS compliance
- Rate limiting: 1-5 seconds between requests
- PII filtering implemented for data protection
- GDPR/CCPA compliance measures in place
- User consent management for data collection

## AI Integration Strategy
- Primary: Claude 4 Sonnet for news summarization
- Secondary: OpenAI GPT-4 for complex reasoning
- Local: spaCy for basic NLP processing
- Confidence scoring for all AI-generated content
- Fallback mechanisms for API failures

## Performance Targets
- 95% daily scraping success rate
- <500ms API response time (95th percentile)
- 90% data accuracy rate
- 99.5% system uptime

## Development Best Practices
1. Use Docker for consistent development environment
2. Follow FastAPI async patterns for performance
3. Implement comprehensive error handling and logging
4. Respect rate limits and ethical scraping practices
5. Use structured logging with contextual information
6. Write tests for all critical functionality
7. Document API changes and database migrations

## Monitoring and Observability
- Structured logging with structlog
- Health check endpoints for all services
- Database query performance monitoring
- Scraping success/failure rate tracking
- AI processing confidence score monitoring
- Rate limiting and quota usage tracking

## Security Considerations
- JWT-based authentication for API access
- Rate limiting on all public endpoints
- Input validation with Pydantic models
- SQL injection prevention with SQLAlchemy
- Secure secret management via environment variables
- CORS configuration for frontend integration