import { apiService } from './api';
import { 
  NewsArticle, 
  NewsResponse, 
  NewsFilters, 
  NewsSortOptions, 
  NewsSearchParams,
  NewsSource,
  TrendingTopic,
  PaginationParams,
  BaseResponse 
} from '../types';

export const newsService = {
  // Get paginated list of news articles
  getNews: async (params: NewsSearchParams = {}): Promise<NewsResponse> => {
    const queryParams: Record<string, any> = {
      page: params.page || 1,
      per_page: params.per_page || 20,
    };

    // Add search query
    if (params.query) {
      queryParams.query = params.query;
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

    return apiService.get<NewsResponse>('/news', queryParams);
  },

  // Get single news article by ID
  getArticle: async (articleId: string): Promise<NewsArticle> => {
    return apiService.get<NewsArticle>(`/news/${articleId}`);
  },

  // Get recent news for dashboard
  getRecentNews: async (limit: number = 5): Promise<NewsArticle[]> => {
    const response = await apiService.get<NewsResponse>('/news/recent', { 
      limit,
      sort_by: 'publish_date',
      sort_direction: 'desc'
    });
    return response.articles;
  },

  // Get news related to a specific company
  getNewsByCompany: async (companyId: string, params: PaginationParams = {}): Promise<NewsResponse> => {
    return apiService.get<NewsResponse>(`/companies/${companyId}/news`, {
      page: params.page || 1,
      per_page: params.per_page || 20,
    });
  },

  // Get news related to a specific deal
  getNewsByDeal: async (dealId: string, params: PaginationParams = {}): Promise<NewsResponse> => {
    return apiService.get<NewsResponse>(`/deals/${dealId}/news`, {
      page: params.page || 1,
      per_page: params.per_page || 20,
    });
  },

  // Search news articles
  searchNews: async (query: string, filters?: NewsFilters, limit: number = 10): Promise<NewsArticle[]> => {
    const queryParams: Record<string, any> = {
      q: query,
      limit,
    };

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

    const response = await apiService.get<NewsResponse>('/news/search', queryParams);
    return response.articles;
  },

  // Get trending news topics
  getTrendingTopics: async (period: 'day' | 'week' | 'month' = 'week'): Promise<TrendingTopic[]> => {
    return apiService.get<TrendingTopic[]>('/news/trending', { period });
  },

  // Get news by category
  getNewsByCategory: async (category: string, params: NewsSearchParams = {}): Promise<NewsResponse> => {
    return newsService.getNews({
      ...params,
      filters: {
        ...params.filters,
        categories: [category],
      },
    });
  },

  // Get news sources
  getNewsSources: async (): Promise<NewsSource[]> => {
    return apiService.get<NewsSource[]>('/news/sources');
  },

  // Get news statistics
  getNewsStats: async (filters?: NewsFilters): Promise<{
    total_articles: number;
    articles_today: number;
    articles_this_week: number;
    articles_by_source: Record<string, number>;
    articles_by_category: Record<string, number>;
    sentiment_distribution: Record<string, number>;
    daily_activity: Array<{ date: string; count: number }>;
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

    return apiService.get('/news/stats', queryParams);
  },

  // Get featured articles
  getFeaturedNews: async (limit: number = 10): Promise<NewsArticle[]> => {
    const response = await apiService.get<NewsResponse>('/news/featured', { limit });
    return response.articles;
  },

  // Get breaking news
  getBreakingNews: async (limit: number = 5): Promise<NewsArticle[]> => {
    const response = await apiService.get<NewsResponse>('/news/breaking', { limit });
    return response.articles;
  },

  // Get available filter options
  getFilterOptions: async (): Promise<{
    sources: string[];
    categories: string[];
    tags: string[];
  }> => {
    return apiService.get('/news/filter-options');
  },

  // Create news alert
  createNewsAlert: async (alertData: {
    name: string;
    keywords: string[];
    filters?: NewsFilters;
    notification_frequency: 'immediate' | 'daily' | 'weekly';
  }): Promise<BaseResponse<{ alert_id: string }>> => {
    return apiService.post('/news/alerts', alertData);
  },

  // Get user's news alerts
  getNewsAlerts: async (): Promise<Array<{
    alert_id: string;
    name: string;
    keywords: string[];
    filters?: NewsFilters;
    notification_frequency: string;
    is_active: boolean;
    created_at: string;
  }>> => {
    return apiService.get('/news/alerts');
  },

  // Update news alert
  updateNewsAlert: async (alertId: string, updates: {
    name?: string;
    keywords?: string[];
    filters?: NewsFilters;
    notification_frequency?: string;
    is_active?: boolean;
  }): Promise<BaseResponse<any>> => {
    return apiService.patch(`/news/alerts/${alertId}`, updates);
  },

  // Delete news alert
  deleteNewsAlert: async (alertId: string): Promise<BaseResponse<any>> => {
    return apiService.delete(`/news/alerts/${alertId}`);
  },

  // Export news to CSV
  exportNews: async (filters?: NewsFilters): Promise<Blob> => {
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

    const response = await apiService.get('/news/export', queryParams);
    return new Blob([response as any], { type: 'text/csv' });
  },

  // Get news sentiment analysis
  getSentimentAnalysis: async (articleIds: string[]): Promise<Array<{
    article_id: string;
    sentiment: 'Positive' | 'Negative' | 'Neutral';
    confidence: number;
    key_phrases: string[];
  }>> => {
    return apiService.post('/news/sentiment', { article_ids: articleIds });
  },

  // Mark article as read
  markAsRead: async (articleId: string): Promise<BaseResponse<any>> => {
    return apiService.post(`/news/${articleId}/read`);
  },

  // Bookmark article
  bookmarkArticle: async (articleId: string): Promise<BaseResponse<any>> => {
    return apiService.post(`/news/${articleId}/bookmark`);
  },

  // Get bookmarked articles
  getBookmarkedArticles: async (params: PaginationParams = {}): Promise<NewsResponse> => {
    return apiService.get<NewsResponse>('/news/bookmarks', {
      page: params.page || 1,
      per_page: params.per_page || 20,
    });
  },

  // Remove bookmark
  removeBookmark: async (articleId: string): Promise<BaseResponse<any>> => {
    return apiService.delete(`/news/${articleId}/bookmark`);
  },
};