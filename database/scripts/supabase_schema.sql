-- MergerTracker Supabase Database Schema
-- This schema creates all necessary tables, indexes, and policies for the MergerTracker application
-- Run this script in your Supabase SQL editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Enable Row Level Security by default
ALTER DATABASE postgres SET row_security = on;

-- Create ENUM types
DO $$ BEGIN
    CREATE TYPE dealstatus AS ENUM (
        'rumored', 'announced', 'pending', 'completed', 'terminated', 'withdrawn'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE dealtype AS ENUM (
        'merger', 'acquisition', 'asset_purchase', 'spin_off', 'joint_venture',
        'management_buyout', 'leveraged_buyout', 'going_private', 'recapitalization', 'other'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE participantrole AS ENUM (
        'acquirer', 'target', 'seller', 'investor', 'bidder', 'joint_venture_partner'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE advisortype AS ENUM (
        'financial', 'legal', 'accounting', 'consulting', 'tax', 'regulatory'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE articletype AS ENUM (
        'news', 'press_release', 'regulatory_filing', 'analyst_report', 'blog_post',
        'social_media', 'transcript', 'interview', 'opinion', 'other'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE contentquality AS ENUM (
        'high', 'medium', 'low', 'unknown'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE sentimentscore AS ENUM (
        'very_positive', 'positive', 'neutral', 'negative', 'very_negative', 'unknown'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_superuser BOOLEAN NOT NULL DEFAULT false,
    last_login TIMESTAMPTZ,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    api_access_token UUID DEFAULT uuid_generate_v4(),
    api_rate_limit INTEGER DEFAULT 1000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create industry_classifications table
CREATE TABLE IF NOT EXISTS public.industry_classifications (
    id SERIAL PRIMARY KEY,
    sic_code VARCHAR(4) NOT NULL UNIQUE,
    sic_description TEXT NOT NULL,
    sic_division VARCHAR(1),
    sic_major_group VARCHAR(2),
    sic_industry_group VARCHAR(3),
    division_description VARCHAR(255),
    major_group_description VARCHAR(255),
    industry_group_description VARCHAR(255),
    naics_code VARCHAR(6),
    naics_description TEXT,
    gics_sector_code VARCHAR(2),
    gics_sector_name VARCHAR(100),
    gics_industry_group_code VARCHAR(4),
    gics_industry_group_name VARCHAR(100),
    gics_industry_code VARCHAR(6),
    gics_industry_name VARCHAR(100),
    gics_sub_industry_code VARCHAR(8),
    gics_sub_industry_name VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_high_tech BOOLEAN NOT NULL DEFAULT false,
    is_financial BOOLEAN NOT NULL DEFAULT false,
    is_healthcare BOOLEAN NOT NULL DEFAULT false,
    ma_activity_level VARCHAR(20),
    typical_deal_size_range VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create companies table
CREATE TABLE IF NOT EXISTS public.companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    ticker_symbol VARCHAR(20),
    exchange VARCHAR(50),
    cusip VARCHAR(9) UNIQUE,
    isin VARCHAR(12) UNIQUE,
    lei VARCHAR(20) UNIQUE,
    cik VARCHAR(10) UNIQUE,
    industry_classification_id INTEGER REFERENCES industry_classifications(id),
    primary_sic_code VARCHAR(4),
    secondary_sic_codes TEXT[], -- Array of SIC codes
    gics_sector VARCHAR(100),
    gics_industry_group VARCHAR(100),
    country VARCHAR(2),
    state_province VARCHAR(100),
    city VARCHAR(100),
    headquarters_address TEXT,
    market_cap NUMERIC(20, 2),
    annual_revenue NUMERIC(20, 2),
    employee_count INTEGER,
    is_public BOOLEAN NOT NULL DEFAULT true,
    is_active BOOLEAN NOT NULL DEFAULT true,
    website VARCHAR(255),
    phone VARCHAR(50),
    description TEXT,
    business_description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create deals table
CREATE TABLE IF NOT EXISTS public.deals (
    id SERIAL PRIMARY KEY,
    deal_id UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    internal_deal_number VARCHAR(50) UNIQUE,
    deal_name VARCHAR(500) NOT NULL,
    deal_type dealtype NOT NULL,
    deal_status dealstatus NOT NULL,
    announcement_date DATE,
    expected_completion_date DATE,
    actual_completion_date DATE,
    rumor_date DATE,
    signing_date DATE,
    regulatory_approval_date DATE,
    shareholder_approval_date DATE,
    termination_date DATE,
    transaction_value NUMERIC(20, 2),
    enterprise_value NUMERIC(20, 2),
    equity_value NUMERIC(20, 2),
    price_per_share NUMERIC(10, 4),
    premium_percent NUMERIC(5, 2),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    exchange_ratio NUMERIC(10, 6),
    cash_component NUMERIC(20, 2),
    stock_component NUMERIC(20, 2),
    payment_method VARCHAR(100),
    deal_structure VARCHAR(100),
    financing_sources TEXT[], -- Array of financing sources
    strategic_rationale TEXT,
    synergies_description TEXT,
    expected_synergies_value NUMERIC(20, 2),
    regulatory_approvals_required TEXT[], -- Array of required approvals
    antitrust_concerns BOOLEAN NOT NULL DEFAULT false,
    regulatory_conditions TEXT,
    is_hostile BOOLEAN NOT NULL DEFAULT false,
    is_cross_border BOOLEAN NOT NULL DEFAULT false,
    is_public_to_private BOOLEAN NOT NULL DEFAULT false,
    involves_private_equity BOOLEAN NOT NULL DEFAULT false,
    primary_geography VARCHAR(2),
    target_geography VARCHAR(2),
    acquirer_geography VARCHAR(2),
    primary_industry_sic VARCHAR(4),
    target_industry_sic VARCHAR(4),
    acquirer_industry_sic VARCHAR(4),
    deal_description TEXT,
    deal_highlights TEXT,
    conditions_precedent TEXT,
    termination_conditions TEXT,
    data_confidence_score NUMERIC(3, 2) DEFAULT 0.5,
    data_source_priority INTEGER NOT NULL DEFAULT 5,
    requires_verification BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create deal_participants table
CREATE TABLE IF NOT EXISTS public.deal_participants (
    id SERIAL PRIMARY KEY,
    deal_id INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    role participantrole NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    ownership_percentage NUMERIC(5, 2),
    post_deal_ownership NUMERIC(5, 2),
    valuation NUMERIC(20, 2),
    shares_outstanding NUMERIC(15, 0),
    shares_transacted NUMERIC(15, 0),
    participant_description TEXT,
    strategic_fit TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(deal_id, company_id, role)
);

-- Create deal_advisors table
CREATE TABLE IF NOT EXISTS public.deal_advisors (
    id SERIAL PRIMARY KEY,
    deal_id INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    advisor_name VARCHAR(255) NOT NULL,
    advisor_type advisortype NOT NULL,
    client_side VARCHAR(50),
    is_lead_advisor BOOLEAN NOT NULL DEFAULT false,
    advisory_fee NUMERIC(15, 2),
    success_fee NUMERIC(15, 2),
    fee_structure VARCHAR(255),
    office_location VARCHAR(100),
    key_personnel TEXT[], -- Array of key personnel names
    practice_area VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create news_articles table
CREATE TABLE IF NOT EXISTS public.news_articles (
    id SERIAL PRIMARY KEY,
    article_id UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    external_id VARCHAR(255) UNIQUE,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    canonical_url TEXT,
    content TEXT,
    summary TEXT,
    excerpt TEXT,
    article_type articletype NOT NULL DEFAULT 'news',
    language VARCHAR(2) NOT NULL DEFAULT 'en',
    word_count INTEGER,
    source_name VARCHAR(255) NOT NULL,
    source_domain VARCHAR(255) NOT NULL,
    source_type VARCHAR(50),
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    author_title VARCHAR(255),
    multiple_authors TEXT[], -- Array of author names
    publish_date TIMESTAMPTZ NOT NULL,
    last_modified_date TIMESTAMPTZ,
    scrape_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    meta_description TEXT,
    meta_keywords TEXT[], -- Array of keywords
    social_shares_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    sentiment_score sentimentscore,
    sentiment_confidence NUMERIC(3, 2),
    content_quality contentquality,
    readability_score NUMERIC(5, 2),
    ma_relevance_score NUMERIC(3, 2),
    contains_deal_info BOOLEAN NOT NULL DEFAULT false,
    deal_confidence_score NUMERIC(3, 2),
    deal_id INTEGER REFERENCES deals(id),
    mentioned_companies TEXT[], -- Array of company names
    mentioned_tickers TEXT[], -- Array of ticker symbols
    geographic_focus TEXT[], -- Array of country codes
    industry_tags TEXT[], -- Array of industry tags
    sic_codes_mentioned TEXT[], -- Array of SIC codes
    ai_extracted_data JSONB,
    ai_processing_version VARCHAR(20),
    ai_confidence_scores JSONB,
    named_entities JSONB,
    key_phrases TEXT[], -- Array of key phrases
    topics TEXT[], -- Array of topics
    is_duplicate BOOLEAN NOT NULL DEFAULT false,
    duplicate_of_id INTEGER REFERENCES news_articles(id),
    data_quality_score NUMERIC(3, 2),
    manual_verification_status VARCHAR(20),
    scraping_source VARCHAR(100) NOT NULL,
    scraping_job_id VARCHAR(100),
    scraping_success BOOLEAN NOT NULL DEFAULT true,
    scraping_errors TEXT[], -- Array of error messages
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_processed BOOLEAN NOT NULL DEFAULT false,
    requires_review BOOLEAN NOT NULL DEFAULT false,
    has_images BOOLEAN NOT NULL DEFAULT false,
    has_videos BOOLEAN NOT NULL DEFAULT false,
    has_documents BOOLEAN NOT NULL DEFAULT false,
    image_urls TEXT[], -- Array of image URLs
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_auth_user_id ON users(auth_user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_api_token ON users(api_access_token);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_industry_sic_code ON industry_classifications(sic_code);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_industry_sic_division ON industry_classifications(sic_division);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_industry_sic_major_group ON industry_classifications(sic_major_group);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_industry_naics_code ON industry_classifications(naics_code);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_name ON companies USING gin(name gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_ticker_symbol ON companies(ticker_symbol);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_cusip ON companies(cusip);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_industry_id ON companies(industry_classification_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_primary_sic ON companies(primary_sic_code);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_country ON companies(country);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_created_at ON companies(created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_deal_id ON deals(deal_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_internal_number ON deals(internal_deal_number);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_name ON deals USING gin(deal_name gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_type ON deals(deal_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_status ON deals(deal_status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_announcement_date ON deals(announcement_date);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_completion_date ON deals(actual_completion_date);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_transaction_value ON deals(transaction_value);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_geography ON deals(primary_geography);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_industry ON deals(primary_industry_sic);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_created_at ON deals(created_at);

-- Composite indexes for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_date_value ON deals(announcement_date, transaction_value);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_status_type ON deals(deal_status, deal_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_geography_industry ON deals(primary_geography, primary_industry_sic);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deal_participants_deal_id ON deal_participants(deal_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deal_participants_company_id ON deal_participants(company_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deal_participants_role ON deal_participants(role);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deal_advisors_deal_id ON deal_advisors(deal_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deal_advisors_name ON deal_advisors(advisor_name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deal_advisors_type ON deal_advisors(advisor_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_article_id ON news_articles(article_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_external_id ON news_articles(external_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_url ON news_articles(url);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_title ON news_articles USING gin(title gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_source_name ON news_articles(source_name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_source_domain ON news_articles(source_domain);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_publish_date ON news_articles(publish_date);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_scrape_date ON news_articles(scrape_date);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_deal_id ON news_articles(deal_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_relevance_score ON news_articles(ma_relevance_score);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_contains_deal ON news_articles(contains_deal_info);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_is_processed ON news_articles(is_processed);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_requires_review ON news_articles(requires_review);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_created_at ON news_articles(created_at);

-- Composite indexes for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_publish_relevance ON news_articles(publish_date, ma_relevance_score);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_source_date ON news_articles(source_domain, publish_date);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_processed_review ON news_articles(is_processed, requires_review);

-- Full-text search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_name_fts ON companies USING gin(to_tsvector('english', name));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_description_fts ON companies USING gin(to_tsvector('english', COALESCE(description, '')));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_name_fts ON deals USING gin(to_tsvector('english', deal_name));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_description_fts ON deals USING gin(to_tsvector('english', COALESCE(deal_description, '')));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_title_fts ON news_articles USING gin(to_tsvector('english', title));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_content_fts ON news_articles USING gin(to_tsvector('english', COALESCE(content, '')));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_summary_fts ON news_articles USING gin(to_tsvector('english', COALESCE(summary, '')));

-- GIN indexes for array columns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_secondary_sic ON companies USING gin(secondary_sic_codes);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_financing_sources ON deals USING gin(financing_sources);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deals_regulatory_approvals ON deals USING gin(regulatory_approvals_required);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_mentioned_companies ON news_articles USING gin(mentioned_companies);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_mentioned_tickers ON news_articles USING gin(mentioned_tickers);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_industry_tags ON news_articles USING gin(industry_tags);

-- JSONB indexes for AI extracted data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_ai_data ON news_articles USING gin(ai_extracted_data);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_named_entities ON news_articles USING gin(named_entities);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language plpgsql;

-- Apply updated_at triggers to all tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_industry_classifications_updated_at BEFORE UPDATE ON industry_classifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deals_updated_at BEFORE UPDATE ON deals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deal_participants_updated_at BEFORE UPDATE ON deal_participants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deal_advisors_updated_at BEFORE UPDATE ON deal_advisors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_news_articles_updated_at BEFORE UPDATE ON news_articles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security Policies

-- Users table - users can only see their own data
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = auth_user_id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = auth_user_id);

-- Industry classifications - read-only for authenticated users
ALTER TABLE industry_classifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Industry classifications are viewable by authenticated users" ON industry_classifications
    FOR SELECT TO authenticated USING (true);

-- Companies - read-only for authenticated users
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Companies are viewable by authenticated users" ON companies
    FOR SELECT TO authenticated USING (true);

-- Deals - read-only for authenticated users
ALTER TABLE deals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Deals are viewable by authenticated users" ON deals
    FOR SELECT TO authenticated USING (true);

-- Deal participants - read-only for authenticated users
ALTER TABLE deal_participants ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Deal participants are viewable by authenticated users" ON deal_participants
    FOR SELECT TO authenticated USING (true);

-- Deal advisors - read-only for authenticated users
ALTER TABLE deal_advisors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Deal advisors are viewable by authenticated users" ON deal_advisors
    FOR SELECT TO authenticated USING (true);

-- News articles - read-only for authenticated users
ALTER TABLE news_articles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "News articles are viewable by authenticated users" ON news_articles
    FOR SELECT TO authenticated USING (true);

-- Create admin policies for service role
CREATE POLICY "Service role can manage all users" ON users
    FOR ALL TO service_role USING (true);

CREATE POLICY "Service role can manage all industry classifications" ON industry_classifications
    FOR ALL TO service_role USING (true);

CREATE POLICY "Service role can manage all companies" ON companies
    FOR ALL TO service_role USING (true);

CREATE POLICY "Service role can manage all deals" ON deals
    FOR ALL TO service_role USING (true);

CREATE POLICY "Service role can manage all deal participants" ON deal_participants
    FOR ALL TO service_role USING (true);

CREATE POLICY "Service role can manage all deal advisors" ON deal_advisors
    FOR ALL TO service_role USING (true);

CREATE POLICY "Service role can manage all news articles" ON news_articles
    FOR ALL TO service_role USING (true);

-- Create views for common queries
CREATE OR REPLACE VIEW deals_with_participants AS
SELECT 
    d.*,
    json_agg(
        json_build_object(
            'company_id', dp.company_id,
            'company_name', c.name,
            'role', dp.role,
            'is_primary', dp.is_primary,
            'ownership_percentage', dp.ownership_percentage
        )
    ) as participants
FROM deals d
LEFT JOIN deal_participants dp ON d.id = dp.deal_id
LEFT JOIN companies c ON dp.company_id = c.id
GROUP BY d.id;

CREATE OR REPLACE VIEW news_with_deals AS
SELECT 
    n.*,
    d.deal_name,
    d.deal_type,
    d.deal_status,
    d.transaction_value
FROM news_articles n
LEFT JOIN deals d ON n.deal_id = d.id;

-- Function to search deals by text
CREATE OR REPLACE FUNCTION search_deals(search_text TEXT, max_results INTEGER DEFAULT 50)
RETURNS TABLE (
    id INTEGER,
    deal_id UUID,
    deal_name VARCHAR(500),
    deal_type dealtype,
    deal_status dealstatus,
    transaction_value NUMERIC(20,2),
    announcement_date DATE,
    rank REAL
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.deal_id,
        d.deal_name,
        d.deal_type,
        d.deal_status,
        d.transaction_value,
        d.announcement_date,
        ts_rank(
            to_tsvector('english', d.deal_name || ' ' || COALESCE(d.deal_description, '')),
            plainto_tsquery('english', search_text)
        ) as rank
    FROM deals d
    WHERE to_tsvector('english', d.deal_name || ' ' || COALESCE(d.deal_description, ''))
          @@ plainto_tsquery('english', search_text)
    ORDER BY rank DESC
    LIMIT max_results;
END;
$$;

-- Function to search companies by text
CREATE OR REPLACE FUNCTION search_companies(search_text TEXT, max_results INTEGER DEFAULT 50)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR(255),
    ticker_symbol VARCHAR(20),
    country VARCHAR(2),
    market_cap NUMERIC(20,2),
    rank REAL
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.name,
        c.ticker_symbol,
        c.country,
        c.market_cap,
        ts_rank(
            to_tsvector('english', c.name || ' ' || COALESCE(c.description, '')),
            plainto_tsquery('english', search_text)
        ) as rank
    FROM companies c
    WHERE to_tsvector('english', c.name || ' ' || COALESCE(c.description, ''))
          @@ plainto_tsquery('english', search_text)
    ORDER BY rank DESC
    LIMIT max_results;
END;
$$;

-- Function to get deal analytics
CREATE OR REPLACE FUNCTION get_deal_analytics(
    date_from DATE DEFAULT NULL,
    date_to DATE DEFAULT NULL,
    group_by_period TEXT DEFAULT 'month'
)
RETURNS TABLE (
    period DATE,
    deal_count BIGINT,
    total_value NUMERIC,
    avg_value NUMERIC,
    max_value NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    date_trunc_format TEXT;
BEGIN
    -- Set date truncation format based on input
    CASE group_by_period
        WHEN 'day' THEN date_trunc_format := 'day';
        WHEN 'week' THEN date_trunc_format := 'week';
        WHEN 'month' THEN date_trunc_format := 'month';
        WHEN 'quarter' THEN date_trunc_format := 'quarter';
        WHEN 'year' THEN date_trunc_format := 'year';
        ELSE date_trunc_format := 'month';
    END CASE;

    RETURN QUERY
    EXECUTE format('
        SELECT 
            date_trunc(%L, announcement_date)::DATE as period,
            COUNT(*)::BIGINT as deal_count,
            COALESCE(SUM(transaction_value), 0) as total_value,
            COALESCE(AVG(transaction_value), 0) as avg_value,
            COALESCE(MAX(transaction_value), 0) as max_value
        FROM deals 
        WHERE announcement_date IS NOT NULL
        AND ($1 IS NULL OR announcement_date >= $1)
        AND ($2 IS NULL OR announcement_date <= $2)
        GROUP BY period
        ORDER BY period DESC
    ', date_trunc_format)
    USING date_from, date_to;
END;
$$;

-- Create API key authentication function
CREATE OR REPLACE FUNCTION authenticate_api_key(api_key UUID)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_id UUID;
BEGIN
    SELECT id INTO user_id 
    FROM users 
    WHERE api_access_token = api_key 
    AND is_active = true;
    
    IF user_id IS NOT NULL THEN
        -- Update last login
        UPDATE users SET last_login = NOW() WHERE id = user_id;
        RETURN user_id;
    ELSE
        RETURN NULL;
    END IF;
END;
$$;

-- Grant permissions to authenticated and service roles
GRANT USAGE ON SCHEMA public TO authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated, service_role;

-- Enable real-time subscriptions for key tables
ALTER publication supabase_realtime ADD TABLE deals;
ALTER publication supabase_realtime ADD TABLE companies;
ALTER publication supabase_realtime ADD TABLE news_articles;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'MergerTracker Supabase schema created successfully!';
    RAISE NOTICE 'Tables created: %, %, %, %, %, %, %', 
        'users', 'industry_classifications', 'companies', 'deals', 
        'deal_participants', 'deal_advisors', 'news_articles';
    RAISE NOTICE 'Indexes created for optimal performance';
    RAISE NOTICE 'Row Level Security enabled with appropriate policies';
    RAISE NOTICE 'Real-time subscriptions enabled for deals, companies, and news_articles';
END
$$;