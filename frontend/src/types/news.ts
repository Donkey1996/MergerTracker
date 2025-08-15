export interface NewsArticle {
  article_id: string;
  headline: string;
  source_name: string;
  source_url?: string;
  author?: string;
  publish_date: string;
  article_url: string;
  content_summary?: string;
  full_content?: string;
  tags?: string[];
  category?: 'M&A' | 'IPO' | 'Financing' | 'Earnings' | 'Regulatory' | 'Market News' | 'Industry Analysis';
  sentiment?: 'Positive' | 'Negative' | 'Neutral';
  related_companies?: RelatedCompany[];
  related_deals?: string[];
  read_time_minutes?: number;
  word_count?: number;
  image_url?: string;
  is_premium?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface RelatedCompany {
  company_id: string;
  company_name: string;
  ticker_symbol?: string;
  relevance_score: number;
  mention_context: string;
}

export interface NewsSource {
  source_id: string;
  source_name: string;
  source_url: string;
  source_type: 'Financial News' | 'Industry Publication' | 'Government' | 'Press Release' | 'Blog' | 'Research';
  credibility_score: number;
  subscription_required: boolean;
  logo_url?: string;
}

export interface NewsFilters {
  source_names?: string[];
  categories?: string[];
  sentiment?: string[];
  publish_date_from?: string;
  publish_date_to?: string;
  related_companies?: string[];
  tags?: string[];
  has_deal_mention?: boolean;
}

export interface NewsSortOptions {
  field: 'publish_date' | 'relevance' | 'source_name' | 'headline';
  direction: 'asc' | 'desc';
}

export interface NewsResponse {
  articles: NewsArticle[];
  total_count: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface NewsSearchParams {
  query?: string;
  filters?: NewsFilters;
  sort?: NewsSortOptions;
  page?: number;
  per_page?: number;
}

export interface TrendingTopic {
  topic: string;
  article_count: number;
  sentiment_score: number;
  growth_rate: number;
  related_keywords: string[];
}