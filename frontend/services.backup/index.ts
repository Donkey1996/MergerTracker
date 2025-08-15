// Re-export all services for easy importing
export * from './api';
export * from './auth';
export * from './deals';
export * from './news';
export * from './companies';

// Dashboard service for aggregated data
import { apiService } from './api';
import { DashboardStats, ActivityItem } from '../types';

export const dashboardService = {
  // Get dashboard overview statistics
  getStats: async (): Promise<DashboardStats> => {
    return apiService.get<DashboardStats>('/dashboard/stats');
  },

  // Get recent activity feed
  getRecentActivity: async (limit: number = 10): Promise<ActivityItem[]> => {
    return apiService.get<ActivityItem[]>('/dashboard/activity', { limit });
  },

  // Get personalized insights
  getInsights: async (): Promise<Array<{
    insight_id: string;
    type: 'trend' | 'alert' | 'recommendation' | 'update';
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
    related_data: any;
    created_at: string;
  }>> => {
    return apiService.get('/dashboard/insights');
  },

  // Get market overview
  getMarketOverview: async (): Promise<{
    market_sentiment: 'bullish' | 'bearish' | 'neutral';
    market_indices: Array<{
      name: string;
      value: number;
      change: number;
      change_percent: number;
    }>;
    ma_activity: {
      deals_announced_today: number;
      deals_completed_today: number;
      total_deal_value_today: number;
    };
    trending_sectors: string[];
  }> => {
    return apiService.get('/dashboard/market-overview');
  },

  // Get user's portfolio performance (if applicable)
  getPortfolioPerformance: async (): Promise<{
    watchlists: Array<{
      watchlist_id: string;
      name: string;
      performance: {
        total_return: number;
        total_return_percent: number;
        day_change: number;
        day_change_percent: number;
      };
    }>;
    alerts_triggered: number;
    news_articles_relevant: number;
  }> => {
    return apiService.get('/dashboard/portfolio');
  },

  // Dismiss insight
  dismissInsight: async (insightId: string): Promise<void> => {
    return apiService.delete(`/dashboard/insights/${insightId}`);
  },
};