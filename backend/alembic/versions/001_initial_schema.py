"""Initial schema with TimescaleDB hypertables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types first
    deal_status_enum = postgresql.ENUM(
        'rumored', 'announced', 'pending', 'completed', 'terminated', 'withdrawn',
        name='dealstatus',
        create_type=False
    )
    deal_status_enum.create(op.get_bind(), checkfirst=True)
    
    deal_type_enum = postgresql.ENUM(
        'merger', 'acquisition', 'asset_purchase', 'spin_off', 'joint_venture',
        'management_buyout', 'leveraged_buyout', 'going_private', 'recapitalization', 'other',
        name='dealtype',
        create_type=False
    )
    deal_type_enum.create(op.get_bind(), checkfirst=True)
    
    participant_role_enum = postgresql.ENUM(
        'acquirer', 'target', 'seller', 'investor', 'bidder', 'joint_venture_partner',
        name='participantrole',
        create_type=False
    )
    participant_role_enum.create(op.get_bind(), checkfirst=True)
    
    advisor_type_enum = postgresql.ENUM(
        'financial', 'legal', 'accounting', 'consulting', 'tax', 'regulatory',
        name='advisortype',
        create_type=False
    )
    advisor_type_enum.create(op.get_bind(), checkfirst=True)
    
    article_type_enum = postgresql.ENUM(
        'news', 'press_release', 'regulatory_filing', 'analyst_report', 'blog_post',
        'social_media', 'transcript', 'interview', 'opinion', 'other',
        name='articletype',
        create_type=False
    )
    article_type_enum.create(op.get_bind(), checkfirst=True)
    
    content_quality_enum = postgresql.ENUM(
        'high', 'medium', 'low', 'unknown',
        name='contentquality',
        create_type=False
    )
    content_quality_enum.create(op.get_bind(), checkfirst=True)
    
    sentiment_score_enum = postgresql.ENUM(
        'very_positive', 'positive', 'neutral', 'negative', 'very_negative', 'unknown',
        name='sentimentscore',
        create_type=False
    )
    sentiment_score_enum.create(op.get_bind(), checkfirst=True)

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)

    # Create industry_classifications table
    op.create_table('industry_classifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sic_code', sa.String(length=4), nullable=False),
        sa.Column('sic_description', sa.Text(), nullable=False),
        sa.Column('sic_division', sa.String(length=1), nullable=True),
        sa.Column('sic_major_group', sa.String(length=2), nullable=True),
        sa.Column('sic_industry_group', sa.String(length=3), nullable=True),
        sa.Column('division_description', sa.String(length=255), nullable=True),
        sa.Column('major_group_description', sa.String(length=255), nullable=True),
        sa.Column('industry_group_description', sa.String(length=255), nullable=True),
        sa.Column('naics_code', sa.String(length=6), nullable=True),
        sa.Column('naics_description', sa.Text(), nullable=True),
        sa.Column('gics_sector_code', sa.String(length=2), nullable=True),
        sa.Column('gics_sector_name', sa.String(length=100), nullable=True),
        sa.Column('gics_industry_group_code', sa.String(length=4), nullable=True),
        sa.Column('gics_industry_group_name', sa.String(length=100), nullable=True),
        sa.Column('gics_industry_code', sa.String(length=6), nullable=True),
        sa.Column('gics_industry_name', sa.String(length=100), nullable=True),
        sa.Column('gics_sub_industry_code', sa.String(length=8), nullable=True),
        sa.Column('gics_sub_industry_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_high_tech', sa.Boolean(), nullable=False),
        sa.Column('is_financial', sa.Boolean(), nullable=False),
        sa.Column('is_healthcare', sa.Boolean(), nullable=False),
        sa.Column('ma_activity_level', sa.String(length=20), nullable=True),
        sa.Column('typical_deal_size_range', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_industry_classifications_sic_code'), 'industry_classifications', ['sic_code'], unique=True)
    op.create_index(op.f('ix_industry_classifications_id'), 'industry_classifications', ['id'], unique=False)
    op.create_index(op.f('ix_industry_classifications_created_at'), 'industry_classifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_industry_classifications_sic_division'), 'industry_classifications', ['sic_division'], unique=False)
    op.create_index(op.f('ix_industry_classifications_sic_major_group'), 'industry_classifications', ['sic_major_group'], unique=False)
    op.create_index(op.f('ix_industry_classifications_sic_industry_group'), 'industry_classifications', ['sic_industry_group'], unique=False)
    op.create_index(op.f('ix_industry_classifications_naics_code'), 'industry_classifications', ['naics_code'], unique=False)

    # Create companies table
    op.create_table('companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('legal_name', sa.String(length=255), nullable=True),
        sa.Column('ticker_symbol', sa.String(length=20), nullable=True),
        sa.Column('exchange', sa.String(length=50), nullable=True),
        sa.Column('cusip', sa.String(length=9), nullable=True),
        sa.Column('isin', sa.String(length=12), nullable=True),
        sa.Column('lei', sa.String(length=20), nullable=True),
        sa.Column('cik', sa.String(length=10), nullable=True),
        sa.Column('industry_classification_id', sa.Integer(), nullable=True),
        sa.Column('primary_sic_code', sa.String(length=4), nullable=True),
        sa.Column('secondary_sic_codes', postgresql.ARRAY(sa.String(length=4)), nullable=True),
        sa.Column('gics_sector', sa.String(length=100), nullable=True),
        sa.Column('gics_industry_group', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=True),
        sa.Column('state_province', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('headquarters_address', sa.Text(), nullable=True),
        sa.Column('market_cap', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('annual_revenue', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('business_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['industry_classification_id'], ['industry_classifications.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_companies_name'), 'companies', ['name'], unique=False)
    op.create_index(op.f('ix_companies_ticker_symbol'), 'companies', ['ticker_symbol'], unique=False)
    op.create_index(op.f('ix_companies_cusip'), 'companies', ['cusip'], unique=True)
    op.create_index(op.f('ix_companies_isin'), 'companies', ['isin'], unique=True)
    op.create_index(op.f('ix_companies_lei'), 'companies', ['lei'], unique=True)
    op.create_index(op.f('ix_companies_cik'), 'companies', ['cik'], unique=True)
    op.create_index(op.f('ix_companies_primary_sic_code'), 'companies', ['primary_sic_code'], unique=False)
    op.create_index(op.f('ix_companies_country'), 'companies', ['country'], unique=False)
    op.create_index(op.f('ix_companies_id'), 'companies', ['id'], unique=False)
    op.create_index(op.f('ix_companies_created_at'), 'companies', ['created_at'], unique=False)

    # Create deals table (TimescaleDB hypertable)
    op.create_table('deals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('internal_deal_number', sa.String(length=50), nullable=True),
        sa.Column('deal_name', sa.String(length=500), nullable=False),
        sa.Column('deal_type', deal_type_enum, nullable=False),
        sa.Column('deal_status', deal_status_enum, nullable=False),
        sa.Column('announcement_date', sa.Date(), nullable=True),
        sa.Column('expected_completion_date', sa.Date(), nullable=True),
        sa.Column('actual_completion_date', sa.Date(), nullable=True),
        sa.Column('rumor_date', sa.Date(), nullable=True),
        sa.Column('signing_date', sa.Date(), nullable=True),
        sa.Column('regulatory_approval_date', sa.Date(), nullable=True),
        sa.Column('shareholder_approval_date', sa.Date(), nullable=True),
        sa.Column('termination_date', sa.Date(), nullable=True),
        sa.Column('transaction_value', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('enterprise_value', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('equity_value', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('price_per_share', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('premium_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('exchange_ratio', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('cash_component', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('stock_component', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('payment_method', sa.String(length=100), nullable=True),
        sa.Column('deal_structure', sa.String(length=100), nullable=True),
        sa.Column('financing_sources', postgresql.ARRAY(sa.String(length=100)), nullable=True),
        sa.Column('strategic_rationale', sa.Text(), nullable=True),
        sa.Column('synergies_description', sa.Text(), nullable=True),
        sa.Column('expected_synergies_value', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('regulatory_approvals_required', postgresql.ARRAY(sa.String(length=100)), nullable=True),
        sa.Column('antitrust_concerns', sa.Boolean(), nullable=False),
        sa.Column('regulatory_conditions', sa.Text(), nullable=True),
        sa.Column('is_hostile', sa.Boolean(), nullable=False),
        sa.Column('is_cross_border', sa.Boolean(), nullable=False),
        sa.Column('is_public_to_private', sa.Boolean(), nullable=False),
        sa.Column('involves_private_equity', sa.Boolean(), nullable=False),
        sa.Column('primary_geography', sa.String(length=2), nullable=True),
        sa.Column('target_geography', sa.String(length=2), nullable=True),
        sa.Column('acquirer_geography', sa.String(length=2), nullable=True),
        sa.Column('primary_industry_sic', sa.String(length=4), nullable=True),
        sa.Column('target_industry_sic', sa.String(length=4), nullable=True),
        sa.Column('acquirer_industry_sic', sa.String(length=4), nullable=True),
        sa.Column('deal_description', sa.Text(), nullable=True),
        sa.Column('deal_highlights', sa.Text(), nullable=True),
        sa.Column('conditions_precedent', sa.Text(), nullable=True),
        sa.Column('termination_conditions', sa.Text(), nullable=True),
        sa.Column('data_confidence_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('data_source_priority', sa.Integer(), nullable=False),
        sa.Column('requires_verification', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deals_deal_id'), 'deals', ['deal_id'], unique=True)
    op.create_index(op.f('ix_deals_internal_deal_number'), 'deals', ['internal_deal_number'], unique=True)
    op.create_index(op.f('ix_deals_deal_name'), 'deals', ['deal_name'], unique=False)
    op.create_index(op.f('ix_deals_deal_type'), 'deals', ['deal_type'], unique=False)
    op.create_index(op.f('ix_deals_deal_status'), 'deals', ['deal_status'], unique=False)
    op.create_index(op.f('ix_deals_announcement_date'), 'deals', ['announcement_date'], unique=False)
    op.create_index(op.f('ix_deals_primary_geography'), 'deals', ['primary_geography'], unique=False)
    op.create_index(op.f('ix_deals_target_geography'), 'deals', ['target_geography'], unique=False)
    op.create_index(op.f('ix_deals_acquirer_geography'), 'deals', ['acquirer_geography'], unique=False)
    op.create_index(op.f('ix_deals_primary_industry_sic'), 'deals', ['primary_industry_sic'], unique=False)
    op.create_index(op.f('ix_deals_target_industry_sic'), 'deals', ['target_industry_sic'], unique=False)
    op.create_index(op.f('ix_deals_acquirer_industry_sic'), 'deals', ['acquirer_industry_sic'], unique=False)
    op.create_index(op.f('ix_deals_id'), 'deals', ['id'], unique=False)
    op.create_index(op.f('ix_deals_created_at'), 'deals', ['created_at'], unique=False)

    # Create deal_participants table
    op.create_table('deal_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('role', participant_role_enum, nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False),
        sa.Column('ownership_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('post_deal_ownership', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('valuation', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('shares_outstanding', sa.Numeric(precision=15, scale=0), nullable=True),
        sa.Column('shares_transacted', sa.Numeric(precision=15, scale=0), nullable=True),
        sa.Column('participant_description', sa.Text(), nullable=True),
        sa.Column('strategic_fit', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deal_participants_deal_id'), 'deal_participants', ['deal_id'], unique=False)
    op.create_index(op.f('ix_deal_participants_company_id'), 'deal_participants', ['company_id'], unique=False)
    op.create_index(op.f('ix_deal_participants_role'), 'deal_participants', ['role'], unique=False)
    op.create_index(op.f('ix_deal_participants_id'), 'deal_participants', ['id'], unique=False)
    op.create_index(op.f('ix_deal_participants_created_at'), 'deal_participants', ['created_at'], unique=False)

    # Create deal_advisors table
    op.create_table('deal_advisors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('advisor_name', sa.String(length=255), nullable=False),
        sa.Column('advisor_type', advisor_type_enum, nullable=False),
        sa.Column('client_side', sa.String(length=50), nullable=True),
        sa.Column('is_lead_advisor', sa.Boolean(), nullable=False),
        sa.Column('advisory_fee', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('success_fee', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('fee_structure', sa.String(length=255), nullable=True),
        sa.Column('office_location', sa.String(length=100), nullable=True),
        sa.Column('key_personnel', postgresql.ARRAY(sa.String(length=255)), nullable=True),
        sa.Column('practice_area', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deal_advisors_deal_id'), 'deal_advisors', ['deal_id'], unique=False)
    op.create_index(op.f('ix_deal_advisors_advisor_name'), 'deal_advisors', ['advisor_name'], unique=False)
    op.create_index(op.f('ix_deal_advisors_advisor_type'), 'deal_advisors', ['advisor_type'], unique=False)
    op.create_index(op.f('ix_deal_advisors_id'), 'deal_advisors', ['id'], unique=False)
    op.create_index(op.f('ix_deal_advisors_created_at'), 'deal_advisors', ['created_at'], unique=False)

    # Create news_articles table (TimescaleDB hypertable)
    op.create_table('news_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('canonical_url', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('article_type', article_type_enum, nullable=False),
        sa.Column('language', sa.String(length=2), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('source_name', sa.String(length=255), nullable=False),
        sa.Column('source_domain', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('author_name', sa.String(length=255), nullable=True),
        sa.Column('author_email', sa.String(length=255), nullable=True),
        sa.Column('author_title', sa.String(length=255), nullable=True),
        sa.Column('multiple_authors', postgresql.ARRAY(sa.String(length=255)), nullable=True),
        sa.Column('publish_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_modified_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scrape_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('meta_keywords', postgresql.ARRAY(sa.String(length=100)), nullable=True),
        sa.Column('social_shares_count', sa.Integer(), nullable=True),
        sa.Column('comments_count', sa.Integer(), nullable=True),
        sa.Column('sentiment_score', sentiment_score_enum, nullable=True),
        sa.Column('sentiment_confidence', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('content_quality', content_quality_enum, nullable=True),
        sa.Column('readability_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('ma_relevance_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('contains_deal_info', sa.Boolean(), nullable=False),
        sa.Column('deal_confidence_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('deal_id', sa.Integer(), nullable=True),
        sa.Column('mentioned_companies', postgresql.ARRAY(sa.String(length=255)), nullable=True),
        sa.Column('mentioned_tickers', postgresql.ARRAY(sa.String(length=20)), nullable=True),
        sa.Column('geographic_focus', postgresql.ARRAY(sa.String(length=2)), nullable=True),
        sa.Column('industry_tags', postgresql.ARRAY(sa.String(length=100)), nullable=True),
        sa.Column('sic_codes_mentioned', postgresql.ARRAY(sa.String(length=4)), nullable=True),
        sa.Column('ai_extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_processing_version', sa.String(length=20), nullable=True),
        sa.Column('ai_confidence_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('named_entities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('key_phrases', postgresql.ARRAY(sa.String(length=255)), nullable=True),
        sa.Column('topics', postgresql.ARRAY(sa.String(length=100)), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False),
        sa.Column('duplicate_of_id', sa.Integer(), nullable=True),
        sa.Column('data_quality_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('manual_verification_status', sa.String(length=20), nullable=True),
        sa.Column('scraping_source', sa.String(length=100), nullable=False),
        sa.Column('scraping_job_id', sa.String(length=100), nullable=True),
        sa.Column('scraping_success', sa.Boolean(), nullable=False),
        sa.Column('scraping_errors', postgresql.ARRAY(sa.String(length=500)), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_processed', sa.Boolean(), nullable=False),
        sa.Column('requires_review', sa.Boolean(), nullable=False),
        sa.Column('has_images', sa.Boolean(), nullable=False),
        sa.Column('has_videos', sa.Boolean(), nullable=False),
        sa.Column('has_documents', sa.Boolean(), nullable=False),
        sa.Column('image_urls', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ),
        sa.ForeignKeyConstraint(['duplicate_of_id'], ['news_articles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_news_articles_article_id'), 'news_articles', ['article_id'], unique=True)
    op.create_index(op.f('ix_news_articles_external_id'), 'news_articles', ['external_id'], unique=True)
    op.create_index(op.f('ix_news_articles_title'), 'news_articles', ['title'], unique=False)
    op.create_index(op.f('ix_news_articles_url'), 'news_articles', ['url'], unique=True)
    op.create_index(op.f('ix_news_articles_article_type'), 'news_articles', ['article_type'], unique=False)
    op.create_index(op.f('ix_news_articles_language'), 'news_articles', ['language'], unique=False)
    op.create_index(op.f('ix_news_articles_source_name'), 'news_articles', ['source_name'], unique=False)
    op.create_index(op.f('ix_news_articles_source_domain'), 'news_articles', ['source_domain'], unique=False)
    op.create_index(op.f('ix_news_articles_author_name'), 'news_articles', ['author_name'], unique=False)
    op.create_index(op.f('ix_news_articles_publish_date'), 'news_articles', ['publish_date'], unique=False)
    op.create_index(op.f('ix_news_articles_sentiment_score'), 'news_articles', ['sentiment_score'], unique=False)
    op.create_index(op.f('ix_news_articles_content_quality'), 'news_articles', ['content_quality'], unique=False)
    op.create_index(op.f('ix_news_articles_ma_relevance_score'), 'news_articles', ['ma_relevance_score'], unique=False)
    op.create_index(op.f('ix_news_articles_contains_deal_info'), 'news_articles', ['contains_deal_info'], unique=False)
    op.create_index(op.f('ix_news_articles_deal_id'), 'news_articles', ['deal_id'], unique=False)
    op.create_index(op.f('ix_news_articles_is_duplicate'), 'news_articles', ['is_duplicate'], unique=False)
    op.create_index(op.f('ix_news_articles_is_processed'), 'news_articles', ['is_processed'], unique=False)
    op.create_index(op.f('ix_news_articles_requires_review'), 'news_articles', ['requires_review'], unique=False)
    op.create_index(op.f('ix_news_articles_id'), 'news_articles', ['id'], unique=False)
    op.create_index(op.f('ix_news_articles_created_at'), 'news_articles', ['created_at'], unique=False)

    # Create TimescaleDB hypertables
    # Note: These SQL commands will only work if TimescaleDB extension is available
    op.execute("""
        SELECT create_hypertable('deals', 'announcement_date', 
                                chunk_time_interval => INTERVAL '1 month',
                                if_not_exists => TRUE);
    """)
    
    op.execute("""
        SELECT create_hypertable('news_articles', 'publish_date', 
                                chunk_time_interval => INTERVAL '1 week',
                                if_not_exists => TRUE);
    """)

    # Create additional performance indexes
    op.create_index('idx_deals_announcement_date_value', 'deals', ['announcement_date', 'transaction_value'], unique=False)
    op.create_index('idx_deals_status_type', 'deals', ['deal_status', 'deal_type'], unique=False)
    op.create_index('idx_deals_geography_industry', 'deals', ['primary_geography', 'primary_industry_sic'], unique=False)
    
    op.create_index('idx_news_publish_relevance', 'news_articles', ['publish_date', 'ma_relevance_score'], unique=False)
    op.create_index('idx_news_source_date', 'news_articles', ['source_domain', 'publish_date'], unique=False)
    op.create_index('idx_news_processed_review', 'news_articles', ['is_processed', 'requires_review'], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_news_processed_review', table_name='news_articles')
    op.drop_index('idx_news_source_date', table_name='news_articles')
    op.drop_index('idx_news_publish_relevance', table_name='news_articles')
    op.drop_index('idx_deals_geography_industry', table_name='deals')
    op.drop_index('idx_deals_status_type', table_name='deals')
    op.drop_index('idx_deals_announcement_date_value', table_name='deals')
    
    # Drop tables
    op.drop_table('news_articles')
    op.drop_table('deal_advisors')
    op.drop_table('deal_participants')
    op.drop_table('deals')
    op.drop_table('companies')
    op.drop_table('industry_classifications')
    op.drop_table('users')
    
    # Drop ENUM types
    sa.Enum(name='sentimentscore').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='contentquality').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='articletype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='advisortype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='participantrole').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='dealtype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='dealstatus').drop(op.get_bind(), checkfirst=True)