import { apiService } from './api';
import { 
  Company, 
  CompanyProfile, 
  CompanySearchResponse, 
  CompanyFilters,
  PaginationParams,
  BaseResponse 
} from '../types';

export interface CompanySearchParams extends PaginationParams {
  filters?: CompanyFilters;
  search?: string;
  sort_by?: 'company_name' | 'market_cap' | 'revenue' | 'founded_year';
  sort_direction?: 'asc' | 'desc';
}

export const companiesService = {
  // Get paginated list of companies
  getCompanies: async (params: CompanySearchParams = {}): Promise<CompanySearchResponse> => {
    const queryParams: Record<string, any> = {
      page: params.page || 1,
      per_page: params.per_page || 20,
    };

    // Add search query
    if (params.search) {
      queryParams.search = params.search;
    }

    // Add sorting
    if (params.sort_by) {
      queryParams.sort_by = params.sort_by;
      queryParams.sort_direction = params.sort_direction || 'asc';
    }

    // Add filters
    if (params.filters) {
      Object.entries(params.filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            queryParams[key] = value.join(',');
          } else {
            queryParams[key] = value;
          }
        }
      });
    }

    return apiService.get<CompanySearchResponse>('/companies', queryParams);
  },

  // Get single company by ID
  getCompany: async (companyId: string): Promise<Company> => {
    return apiService.get<Company>(`/companies/${companyId}`);
  },

  // Get detailed company profile
  getCompanyProfile: async (companyId: string): Promise<CompanyProfile> => {
    return apiService.get<CompanyProfile>(`/companies/${companyId}/profile`);
  },

  // Search companies with autocomplete
  searchCompanies: async (query: string, limit: number = 10): Promise<Company[]> => {
    const response = await apiService.get<CompanySearchResponse>('/companies/search', {
      q: query,
      limit,
    });
    return response.companies;
  },

  // Get company by ticker symbol
  getCompanyByTicker: async (ticker: string): Promise<Company> => {
    return apiService.get<Company>(`/companies/ticker/${ticker}`);
  },

  // Get companies by industry
  getCompaniesByIndustry: async (industry: string, params: PaginationParams = {}): Promise<CompanySearchResponse> => {
    return companiesService.getCompanies({
      ...params,
      filters: {
        industry_sector: [industry],
      },
    });
  },

  // Get trending companies
  getTrendingCompanies: async (period: 'day' | 'week' | 'month' = 'week'): Promise<Company[]> => {
    const response = await apiService.get<CompanySearchResponse>('/companies/trending', {
      period,
    });
    return response.companies;
  },

  // Get recently IPO'd companies
  getRecentIPOs: async (limit: number = 10): Promise<Company[]> => {
    const response = await apiService.get<CompanySearchResponse>('/companies/recent-ipos', {
      limit,
    });
    return response.companies;
  },

  // Get top acquirers
  getTopAcquirers: async (period: 'year' | 'quarter' | 'month' = 'year', limit: number = 10): Promise<Array<{
    company: Company;
    deal_count: number;
    total_deal_value: number;
    avg_deal_size: number;
  }>> => {
    return apiService.get('/companies/top-acquirers', {
      period,
      limit,
    });
  },

  // Get top targets
  getTopTargets: async (period: 'year' | 'quarter' | 'month' = 'year', limit: number = 10): Promise<Array<{
    company: Company;
    deal_count: number;
    total_deal_value: number;
    avg_deal_size: number;
  }>> => {
    return apiService.get('/companies/top-targets', {
      period,
      limit,
    });
  },

  // Get company statistics
  getCompanyStats: async (filters?: CompanyFilters): Promise<{
    total_companies: number;
    public_companies: number;
    private_companies: number;
    companies_by_industry: Record<string, number>;
    companies_by_region: Record<string, number>;
    avg_market_cap: number;
    median_market_cap: number;
    companies_with_recent_deals: number;
  }> => {
    const queryParams: Record<string, any> = {};
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            queryParams[key] = value.join(',');
          } else {
            queryParams[key] = value;
          }
        }
      });
    }

    return apiService.get('/companies/stats', queryParams);
  },

  // Get peer companies
  getPeerCompanies: async (companyId: string, limit: number = 10): Promise<Company[]> => {
    const response = await apiService.get<CompanySearchResponse>(`/companies/${companyId}/peers`, {
      limit,
    });
    return response.companies;
  },

  // Get company competitors
  getCompetitors: async (companyId: string, limit: number = 10): Promise<Company[]> => {
    const response = await apiService.get<CompanySearchResponse>(`/companies/${companyId}/competitors`, {
      limit,
    });
    return response.companies;
  },

  // Get available filter options
  getFilterOptions: async (): Promise<{
    industries: string[];
    regions: string[];
    company_types: string[];
    exchanges: string[];
  }> => {
    return apiService.get('/companies/filter-options');
  },

  // Create company watchlist
  createWatchlist: async (watchlistData: {
    name: string;
    description?: string;
    company_ids: string[];
  }): Promise<BaseResponse<{ watchlist_id: string }>> => {
    return apiService.post('/companies/watchlists', watchlistData);
  },

  // Get user's watchlists
  getWatchlists: async (): Promise<Array<{
    watchlist_id: string;
    name: string;
    description?: string;
    company_count: number;
    created_at: string;
    updated_at: string;
  }>> => {
    return apiService.get('/companies/watchlists');
  },

  // Get watchlist details
  getWatchlist: async (watchlistId: string): Promise<{
    watchlist_id: string;
    name: string;
    description?: string;
    companies: Company[];
    created_at: string;
    updated_at: string;
  }> => {
    return apiService.get(`/companies/watchlists/${watchlistId}`);
  },

  // Add company to watchlist
  addToWatchlist: async (watchlistId: string, companyId: string): Promise<BaseResponse<any>> => {
    return apiService.post(`/companies/watchlists/${watchlistId}/companies`, {
      company_id: companyId,
    });
  },

  // Remove company from watchlist
  removeFromWatchlist: async (watchlistId: string, companyId: string): Promise<BaseResponse<any>> => {
    return apiService.delete(`/companies/watchlists/${watchlistId}/companies/${companyId}`);
  },

  // Update watchlist
  updateWatchlist: async (watchlistId: string, updates: {
    name?: string;
    description?: string;
  }): Promise<BaseResponse<any>> => {
    return apiService.patch(`/companies/watchlists/${watchlistId}`, updates);
  },

  // Delete watchlist
  deleteWatchlist: async (watchlistId: string): Promise<BaseResponse<any>> => {
    return apiService.delete(`/companies/watchlists/${watchlistId}`);
  },

  // Export companies to CSV
  exportCompanies: async (filters?: CompanyFilters): Promise<Blob> => {
    const queryParams: Record<string, any> = { format: 'csv' };
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            queryParams[key] = value.join(',');
          } else {
            queryParams[key] = value;
          }
        }
      });
    }

    const response = await apiService.get('/companies/export', queryParams);
    return new Blob([response as any], { type: 'text/csv' });
  },

  // Follow company
  followCompany: async (companyId: string): Promise<BaseResponse<any>> => {
    return apiService.post(`/companies/${companyId}/follow`);
  },

  // Unfollow company
  unfollowCompany: async (companyId: string): Promise<BaseResponse<any>> => {
    return apiService.delete(`/companies/${companyId}/follow`);
  },

  // Get followed companies
  getFollowedCompanies: async (params: PaginationParams = {}): Promise<CompanySearchResponse> => {
    return apiService.get<CompanySearchResponse>('/companies/following', {
      page: params.page || 1,
      per_page: params.per_page || 20,
    });
  },

  // Get company activity feed
  getCompanyActivity: async (companyId: string, params: PaginationParams = {}): Promise<{
    activities: Array<{
      activity_id: string;
      type: 'deal_announced' | 'deal_completed' | 'news_published' | 'financial_update';
      title: string;
      description: string;
      timestamp: string;
      related_data: any;
    }>;
    total_count: number;
    page: number;
    per_page: number;
  }> => {
    return apiService.get(`/companies/${companyId}/activity`, {
      page: params.page || 1,
      per_page: params.per_page || 20,
    });
  },
};