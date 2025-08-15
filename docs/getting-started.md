# Getting Started with MergerTracker

## Prerequisites

Before setting up MergerTracker, ensure you have the following installed:

- **Python 3.11+**
- **Node.js 18+** and npm
- **PostgreSQL 15+** with TimescaleDB extension
- **Redis 6+**
- **Docker and Docker Compose** (recommended for development)

## Quick Start with Docker

The fastest way to get MergerTracker running is using Docker Compose:

### 1. Clone the Repository
```bash
git clone git@github.com:Donkey1996/MergerTracker.git
cd MergerTracker
```

### 2. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 3. Start All Services
```bash
docker-compose up -d
```

This will start:
- PostgreSQL with TimescaleDB on port 5432
- Redis on port 6379
- FastAPI backend on port 8000
- React frontend on port 3000

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health

## Manual Setup

### Backend Setup

1. **Create Virtual Environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Set Up Database**
```bash
# Install TimescaleDB extension in PostgreSQL
CREATE EXTENSION IF NOT EXISTS timescaledb;

# Run migrations
alembic upgrade head
```

4. **Start Backend Server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Install Dependencies**
```bash
cd frontend
npm install
```

2. **Start Development Server**
```bash
npm start
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root with the following:

```env
# Database
DATABASE_URL=postgresql://mergertracker:password@localhost:5432/mergertracker

# Redis
REDIS_URL=redis://localhost:6379

# AI APIs (at least one required)
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key

# Application
SECRET_KEY=your_secret_key_here
ENVIRONMENT=development
```

### API Keys Setup

1. **Claude API Key**
   - Sign up at https://console.anthropic.com/
   - Create a new API key
   - Add to `.env` as `CLAUDE_API_KEY`

2. **OpenAI API Key** (optional, for fallback)
   - Sign up at https://platform.openai.com/
   - Create a new API key
   - Add to `.env` as `OPENAI_API_KEY`

## Database Setup

### PostgreSQL with TimescaleDB

1. **Install PostgreSQL 15+**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-15

# macOS with Homebrew
brew install postgresql@15
```

2. **Install TimescaleDB**
```bash
# Add TimescaleDB repository
echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main" | sudo tee /etc/apt/sources.list.d/timescaledb.list
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
sudo apt-get update

# Install TimescaleDB
sudo apt-get install timescaledb-2-postgresql-15
```

3. **Create Database**
```sql
CREATE DATABASE mergertracker;
CREATE USER mergertracker WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mergertracker TO mergertracker;

-- Connect to the database and enable TimescaleDB
\c mergertracker;
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

## Running Tests

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Development Workflow

### 1. Daily Development
```bash
# Start all services
docker-compose up -d

# Watch logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Database Migrations
```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head
```

### 3. Adding New Dependencies

**Backend:**
```bash
pip install package_name
pip freeze > requirements.txt
```

**Frontend:**
```bash
npm install package_name
```

## Next Steps

Once you have the basic setup running:

1. **Configure News Sources** - Set up your preferred financial news sources for scraping
2. **Set Up Monitoring** - Configure logging and monitoring for production use
3. **Customize AI Models** - Fine-tune summarization and extraction models
4. **Deploy to Production** - Follow the deployment guide for cloud deployment

## Troubleshooting

### Common Issues

1. **TimescaleDB Extension Error**
   - Ensure TimescaleDB is properly installed
   - Check PostgreSQL logs for detailed error messages

2. **API Key Issues**
   - Verify API keys are correctly set in `.env`
   - Check API key permissions and rate limits

3. **Port Conflicts**
   - Ensure ports 3000, 5432, 6379, and 8000 are available
   - Modify port mappings in `docker-compose.yml` if needed

4. **Scraping Issues**
   - Check robots.txt compliance
   - Verify user agent settings
   - Monitor rate limiting

### Getting Help

- Check the [Troubleshooting Guide](./troubleshooting.md)
- Review [API Documentation](./api.md)
- Submit issues on GitHub

## Development Tips

1. **Use Docker for consistency** - Ensures identical development environments
2. **Monitor logs** - Use structured logging to track scraping and processing
3. **Test incrementally** - Start with single news sources before scaling
4. **Respect rate limits** - Always follow ethical scraping practices