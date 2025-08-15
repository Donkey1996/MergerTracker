export interface Company {
  company_id: string;
  company_name: string;
  ticker_symbol?: string;
  industry_sic_code?: string;
  industry_sector?: string;
  website_domain?: string;
  headquarters_location?: string;
  market_cap?: number;
  revenue?: number;
  employees_count?: number;
  description?: string;
  founded_year?: number;
  is_public?: boolean;
  exchange?: string;
  logo_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CompanyProfile extends Company {
  recent_deals: CompanyDeal[];
  deal_count: number;
  total_deal_value: number;
  key_executives: Executive[];
  financial_metrics: FinancialMetrics;
  stock_data?: StockData;
}

export interface CompanyDeal {
  deal_id: string;
  deal_type: string;
  deal_status: string;
  deal_value?: number;
  announcement_date: string;
  completion_date?: string;
  role: 'Target' | 'Acquirer' | 'Joint Venture Partner';
  counterparty_name: string;
}

export interface Executive {
  name: string;
  title: string;
  tenure?: number;
}

export interface FinancialMetrics {
  revenue_ttm?: number;
  ebitda_ttm?: number;
  net_income_ttm?: number;
  total_assets?: number;
  total_debt?: number;
  enterprise_value?: number;
  pe_ratio?: number;
  ev_revenue?: number;
  ev_ebitda?: number;
}

export interface StockData {
  current_price: number;
  change_1d: number;
  change_1d_percent: number;
  change_52w: number;
  change_52w_percent: number;
  volume: number;
  market_cap: number;
  fifty_two_week_high: number;
  fifty_two_week_low: number;
}

export interface CompanyFilters {
  industry_sector?: string[];
  geographic_region?: string[];
  market_cap_min?: number;
  market_cap_max?: number;
  is_public?: boolean;
  has_recent_deals?: boolean;
}

export interface CompanySearchResponse {
  companies: Company[];
  total_count: number;
  page: number;
  per_page: number;
  total_pages: number;
}