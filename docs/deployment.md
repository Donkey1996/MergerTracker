# Deployment Guide

This guide covers deploying MergerTracker to various cloud platforms, with specific focus on free hosting options like Vercel.

## 🚀 Vercel Deployment (Recommended for Frontend)

### Prerequisites
- Vercel account
- GitHub repository
- External PostgreSQL database (Supabase, Neon, or PlanetScale)
- Redis instance (Upstash or Redis Cloud)

### Setup Steps

1. **Connect Repository to Vercel**
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   
   # Link project
   vercel link
   ```

2. **Configure Environment Variables**
   In Vercel dashboard, add:
   ```env
   DATABASE_URL=postgresql://username:password@host:5432/database
   REDIS_URL=redis://username:password@host:6379
   CLAUDE_API_KEY=your_claude_api_key
   SECRET_KEY=your_secret_key
   ENVIRONMENT=production
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

### Vercel Configuration
The `vercel.json` file is configured to:
- Build backend as Python serverless function
- Build frontend as static React app
- Route `/api/*` to backend
- Route everything else to frontend

## 🚂 Railway Deployment

Railway provides excellent full-stack deployment with PostgreSQL and Redis.

### Setup Steps

1. **Connect to Railway**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login and link
   railway login
   railway link
   ```

2. **Add Services**
   ```bash
   # Add PostgreSQL
   railway add postgresql
   
   # Add Redis
   railway add redis
   ```

3. **Deploy**
   ```bash
   railway up
   ```

Railway automatically detects the `railway.toml` configuration.

## 🎨 Render Deployment

Render offers generous free tier with automatic SSL and CDN.

### Setup Steps

1. **Connect GitHub Repository**
   - Go to Render dashboard
   - Connect your GitHub repository

2. **Import render.yaml**
   Render will automatically detect `deployment/render.yaml` and create:
   - Backend web service
   - Frontend static site
   - PostgreSQL database
   - Redis instance

3. **Configure Environment Variables**
   Set the required environment variables in Render dashboard.

## 🐳 Docker Deployment

### Local Docker Setup
```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Docker
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

## ☁️ Cloud Provider Options

### AWS Deployment
- **Backend**: AWS Lambda + API Gateway
- **Frontend**: CloudFront + S3
- **Database**: RDS PostgreSQL
- **Cache**: ElastiCache Redis

### Google Cloud Deployment
- **Backend**: Cloud Run
- **Frontend**: Firebase Hosting
- **Database**: Cloud SQL PostgreSQL
- **Cache**: Memorystore Redis

### Azure Deployment
- **Backend**: Azure Functions
- **Frontend**: Static Web Apps
- **Database**: Azure Database for PostgreSQL
- **Cache**: Azure Cache for Redis

## 🗄️ Database Setup

### Supabase (Recommended Free Option)
1. Create account at supabase.com
2. Create new project
3. Get connection string from Settings > Database
4. Enable TimescaleDB extension if needed

### Neon (PostgreSQL)
1. Create account at neon.tech
2. Create database
3. Get connection string
4. No TimescaleDB support (use regular PostgreSQL features)

### PlanetScale (MySQL Alternative)
Note: Requires schema changes for MySQL compatibility

## 🔄 Cache Setup

### Upstash Redis (Free Tier)
1. Create account at upstash.com
2. Create Redis database
3. Get connection string
4. 10,000 requests/day free

### Redis Cloud
1. Create account at redis.com
2. Create free database (30MB)
3. Get connection string

## 🔐 Environment Variables

### Required Variables
```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Cache
REDIS_URL=redis://host:6379

# AI Services
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key  # Optional fallback

# Application
SECRET_KEY=your_secret_key
ENVIRONMENT=production

# Optional
SENTRY_DSN=your_sentry_dsn
```

### Frontend Environment Variables
```env
REACT_APP_API_URL=https://your-backend-url.com
```

## 📊 Monitoring and Logging

### Sentry Integration
```bash
# Add to requirements.txt
sentry-sdk[fastapi]==1.38.0

# Configure in settings.py
SENTRY_DSN=your_sentry_dsn
```

### Health Checks
All deployment configurations include health check endpoints:
- Backend: `/health`
- Database connectivity check
- Redis connectivity check

## 🔄 CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Timeout**
   - Check firewall settings
   - Verify connection string format
   - Test connectivity from deployment platform

2. **CORS Issues**
   - Update `ALLOWED_ORIGINS` in settings
   - Verify frontend URL configuration

3. **Memory Limits**
   - Optimize Docker image size
   - Use multi-stage builds
   - Monitor memory usage

4. **Cold Starts (Serverless)**
   - Implement health check warming
   - Use connection pooling
   - Optimize import statements

### Performance Optimization

1. **Frontend**
   - Enable gzip compression
   - Use CDN for static assets
   - Implement lazy loading

2. **Backend**
   - Connection pooling
   - Query optimization
   - Caching strategies

3. **Database**
   - Index optimization
   - Query performance monitoring
   - Connection limits

## 💰 Cost Optimization

### Free Tier Recommendations
- **Frontend**: Vercel (hobby plan)
- **Backend**: Railway (500 hours/month)
- **Database**: Supabase (500MB free)
- **Cache**: Upstash Redis (10k requests/day)
- **Monitoring**: Sentry (5k events/month)

### Scaling Considerations
- Monitor usage metrics
- Implement rate limiting
- Use database query optimization
- Consider read replicas for scaling

## 🔒 Security Checklist

- [ ] Environment variables properly configured
- [ ] Database connection secured (SSL)
- [ ] API rate limiting enabled
- [ ] CORS properly configured
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Input validation implemented
- [ ] SQL injection protection
- [ ] Authentication tokens secured

## 📈 Post-Deployment

1. **Monitor Performance**
   - Set up alerts for errors
   - Monitor response times
   - Track user engagement

2. **Backup Strategy**
   - Database regular backups
   - Environment variable backups
   - Code repository protection

3. **Updates and Maintenance**
   - Automated dependency updates
   - Security patch management
   - Performance monitoring