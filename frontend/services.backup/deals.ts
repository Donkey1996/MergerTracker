import { apiService } from './api';
import { 
  Deal, 
  DealsResponse, 
  DealFilters, 
  DealSortOptions, 
  PaginationParams,
  BaseResponse 
} from '../types';

export interface DealSearchParams extends PaginationParams {
  filters?: DealFilters;
  sort?: DealSortOptions;
  search?: string;
}

export const dealsService = {
  // Get paginated list of deals
  getDeals: async (params: DealSearchParams = {}): Promise<DealsResponse> => {
    const queryParams: Record<string, any> = {
      page: params.page || 1,
      per_page: params.per_page || 20,
    };

    // Add search query
    if (params.search) {
      queryParams.search = params.search;
    }

    // Add sorting
    if (params.sort) {
      queryParams.sort_by = params.sort.field;
      queryParams.sort_direction = params.sort.direction;
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

    return apiService.get<DealsResponse>('/deals', queryParams);
  },

  // Get single deal by ID
  getDeal: async (dealId: string): Promise<Deal> => {
    return apiService.get<Deal>(`/deals/${dealId}`);
  },

  // Get recent deals for dashboard
  getRecentDeals: async (limit: number = 5): Promise<Deal[]> => {
    const response = await apiService.get<DealsResponse>('/deals/recent', { 
      limit,
      sort_by: 'announcement_date',
      sort_direction: 'desc'
    });
    return response.deals;
  },

  // Get deals by company
  getDealsByCompany: async (companyId: string, params: PaginationParams = {}): Promise<DealsResponse> => {
    return apiService.get<DealsResponse>(`/companies/${companyId}/deals`, {
      page: params.page || 1,
      per_page: params.per_page || 20,
    });
  },

  // Get deal statistics
  getDealStats: async (filters?: DealFilters): Promise<{
    total_deals: number;
    total_value: number;
    avg_deal_size: number;
    deals_by_status: Record<string, number>;
    deals_by_type: Record<string, number>;
    deals_by_industry: Record<string, number>;
    monthly_activity: Array<{ month: string; count: number; value: number }>;
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

    return apiService.get('/deals/stats', queryParams);
  },

  // Search deals with suggestions
  searchDeals: async (query: string, limit: number = 10): Promise<Deal[]> => {
    const response = await apiService.get<DealsResponse>('/deals/search', {
      q: query,
      limit,
    });
    return response.deals;
  },

  // Get trending deals
  getTrendingDeals: async (period: 'day' | 'week' | 'month' = 'week'): Promise<Deal[]> => {
    const response = await apiService.get<DealsResponse>('/deals/trending', {
      period,
    });
    return response.deals;
  },

  // Get deals by industry
  getDealsByIndustry: async (industry: string, params: DealSearchParams = {}): Promise<DealsResponse> => {
    return dealsService.getDeals({
      ...params,
      filters: {
        ...params.filters,
        industry_sector: [industry],
      },
    });
  },

  // Export deals to CSV
  exportDeals: async (filters?: DealFilters): Promise<Blob> => {
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

    const response = await apiService.get('/deals/export', queryParams);
    return new Blob([response as any], { type: 'text/csv' });
  },

  // Get available filter options
  getFilterOptions: async (): Promise<{
    deal_types: string[];
    deal_statuses: string[];
    industries: string[];
    regions: string[];
  }> => {
    return apiService.get('/deals/filter-options');
  },

  // Create deal alert
  createDealAlert: async (alertData: {
    name: string;
    filters: DealFilters;
    notification_frequency: 'immediate' | 'daily' | 'weekly';
  }): Promise<BaseResponse<{ alert_id: string }>> => {
    return apiService.post('/deals/alerts', alertData);
  },

  // Get user's deal alerts
  getDealAlerts: async (): Promise<Array<{
    alert_id: string;
    name: string;
    filters: DealFilters;
    notification_frequency: string;
    is_active: boolean;
    created_at: string;
  }>> => {
    return apiService.get('/deals/alerts');
  },

  // Update deal alert
  updateDealAlert: async (alertId: string, updates: {
    name?: string;
    filters?: DealFilters;
    notification_frequency?: string;
    is_active?: boolean;
  }): Promise<BaseResponse<any>> => {
    return apiService.patch(`/deals/alerts/${alertId}`, updates);
  },

  // Delete deal alert
  deleteDealAlert: async (alertId: string): Promise<BaseResponse<any>> => {
    return apiService.delete(`/deals/alerts/${alertId}`);
  },
};