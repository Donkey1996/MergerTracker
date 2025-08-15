// Re-export all types for easy importing
export * from './deal';
export * from './company';
export * from './news';
export * from './auth';

// Common utility types
export interface PaginationParams {
  page?: number;
  per_page?: number;
}

export interface SortParams {
  sort_by?: string;
  sort_direction?: 'asc' | 'desc';
}

export interface BaseResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total_count: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, string[]>;
  status_code: number;
}

export interface DashboardStats {
  total_deals: number;
  deals_this_month: number;
  total_deal_value: number;
  active_companies: number;
  news_articles_today: number;
  trending_industries: string[];
  recent_activity: ActivityItem[];
}

export interface ActivityItem {
  id: string;
  type: 'deal_announced' | 'deal_completed' | 'company_ipo' | 'news_published';
  title: string;
  description: string;
  timestamp: string;
  related_url?: string;
  companies_involved?: string[];
}

export interface SearchSuggestion {
  value: string;
  type: 'company' | 'deal' | 'industry' | 'person';
  subtitle?: string;
  highlight?: string;
}

export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
}

// Theme-related types
export interface ThemeMode {
  mode: 'light' | 'dark';
}

export interface AppConfig {
  api_base_url: string;
  app_name: string;
  app_version: string;
  environment: 'development' | 'staging' | 'production';
  features: {
    dark_mode: boolean;
    analytics: boolean;
    notifications: boolean;
    export_data: boolean;
  };
}