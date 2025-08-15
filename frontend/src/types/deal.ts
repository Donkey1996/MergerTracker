// Deal-related TypeScript interfaces

export enum DealStatus {
  ANNOUNCED = 'announced',
  PENDING = 'pending',
  COMPLETED = 'completed',
  WITHDRAWN = 'withdrawn',
  TERMINATED = 'terminated',
}

export enum DealType {
  MERGER = 'merger',
  ACQUISITION = 'acquisition',
  LBO = 'lbo',
  SPINOFF = 'spinoff',
  JOINT_VENTURE = 'joint_venture',
  ASSET_PURCHASE = 'asset_purchase',
  MANAGEMENT_BUYOUT = 'management_buyout',
}

export enum PaymentMethod {
  CASH = 'cash',
  STOCK = 'stock',
  COMBINATION = 'combination',
  DEBT_ASSUMPTION = 'debt_assumption',
}

export interface DealCompany {
  company_id: string;
  company_name: string;
  ticker_symbol?: string;
  industry_sic_code?: string;
  website_domain?: string;
  employee_count?: number;
  description?: string;
  headquarters_location?: string;
  founded_year?: number;
  market_cap?: string;
  created_at: string;
  updated_at: string;
}

export interface DealParticipant {
  participant_id: string;
  target_company?: DealCompany;
  acquirer_company?: DealCompany;
  ownership_percentage?: number;
  participation_type: string;
  created_at: string;
}

export interface Deal {
  deal_id: string;
  announcement_date: string;
  completion_date?: string;
  deal_status: DealStatus;
  deal_type: DealType;
  deal_value?: number;
  enterprise_value?: number;
  payment_method?: PaymentMethod;
  deal_headline?: string;
  deal_description?: string;
  deal_rationale?: string;
  purchase_price_multiple?: number;
  revenue_multiple?: number;
  ebitda_multiple?: number;
  stock_premium_percentage?: number;
  financial_advisors?: string;
  legal_advisors?: string;
  advisory_fees?: number;
  regulatory_approvals_required?: string;
  approval_status?: string;
  source_confidence_score?: number;
  created_at: string;
  updated_at: string;
  participants: DealParticipant[];
}

export interface DealListResponse {
  deals: Deal[];
  total: number;
  skip: number;
  limit: number;
}

export interface DealFilters {
  status?: DealStatus;
  deal_type?: DealType;
  min_value?: number;
  max_value?: number;
  start_date?: string;
  end_date?: string;
  search?: string;
}

export interface DealSummary {
  deal_id: string;
  announcement_date: string;
  deal_status: DealStatus;
  deal_type: DealType;
  deal_value?: number;
  deal_headline?: string;
  target_company?: string;
  acquirer_company?: string;
}