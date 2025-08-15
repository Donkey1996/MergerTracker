import { apiService, setTokens, clearTokens } from './api';
import { 
  User, 
  LoginRequest, 
  RegisterRequest, 
  AuthResponse, 
  ForgotPasswordRequest,
  ResetPasswordRequest,
  ChangePasswordRequest,
  UserPreferences,
  BaseResponse 
} from '../types';

export const authService = {
  // Login user
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response = await apiService.post<AuthResponse>('/auth/login', credentials);
    setTokens({
      access_token: response.access_token,
      refresh_token: response.refresh_token,
    });
    return response;
  },

  // Register new user
  register: async (userData: RegisterRequest): Promise<AuthResponse> => {
    const response = await apiService.post<AuthResponse>('/auth/register', userData);
    setTokens({
      access_token: response.access_token,
      refresh_token: response.refresh_token,
    });
    return response;
  },

  // Logout user
  logout: async (): Promise<void> => {
    try {
      await apiService.post('/auth/logout');
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error);
    } finally {
      clearTokens();
    }
  },

  // Refresh access token
  refreshToken: async (refreshToken: string): Promise<AuthResponse> => {
    const response = await apiService.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    setTokens({
      access_token: response.access_token,
      refresh_token: response.refresh_token,
    });
    return response;
  },

  // Get current user profile
  getCurrentUser: async (): Promise<User> => {
    return apiService.get<User>('/auth/me');
  },

  // Update user profile
  updateProfile: async (updates: Partial<User>): Promise<BaseResponse<User>> => {
    return apiService.patch<BaseResponse<User>>('/auth/profile', updates);
  },

  // Change password
  changePassword: async (request: ChangePasswordRequest): Promise<BaseResponse<any>> => {
    return apiService.post<BaseResponse<any>>('/auth/change-password', request);
  },

  // Forgot password
  forgotPassword: async (request: ForgotPasswordRequest): Promise<BaseResponse<any>> => {
    return apiService.post<BaseResponse<any>>('/auth/forgot-password', request);
  },

  // Reset password
  resetPassword: async (request: ResetPasswordRequest): Promise<BaseResponse<any>> => {
    return apiService.post<BaseResponse<any>>('/auth/reset-password', request);
  },

  // Verify email
  verifyEmail: async (token: string): Promise<BaseResponse<any>> => {
    return apiService.post<BaseResponse<any>>('/auth/verify-email', { token });
  },

  // Resend verification email
  resendVerificationEmail: async (): Promise<BaseResponse<any>> => {
    return apiService.post<BaseResponse<any>>('/auth/resend-verification');
  },

  // Update user preferences
  updatePreferences: async (preferences: Partial<UserPreferences>): Promise<BaseResponse<UserPreferences>> => {
    return apiService.patch<BaseResponse<UserPreferences>>('/auth/preferences', preferences);
  },

  // Get user preferences
  getPreferences: async (): Promise<UserPreferences> => {
    return apiService.get<UserPreferences>('/auth/preferences');
  },

  // Delete user account
  deleteAccount: async (password: string): Promise<BaseResponse<any>> => {
    return apiService.post<BaseResponse<any>>('/auth/delete-account', { password });
  },

  // Get user subscription info
  getSubscription: async (): Promise<{
    subscription_tier: string;
    subscription_status: 'active' | 'cancelled' | 'expired' | 'trial';
    subscription_expires_at?: string;
    features: {
      max_watchlists: number;
      max_alerts: number;
      export_data: boolean;
      advanced_analytics: boolean;
      api_access: boolean;
    };
  }> => {
    return apiService.get('/auth/subscription');
  },

  // Get user activity log
  getActivityLog: async (params: { page?: number; per_page?: number } = {}): Promise<{
    activities: Array<{
      activity_id: string;
      type: 'login' | 'logout' | 'profile_update' | 'password_change' | 'data_export';
      description: string;
      ip_address: string;
      user_agent: string;
      timestamp: string;
    }>;
    total_count: number;
    page: number;
    per_page: number;
  }> => {
    return apiService.get('/auth/activity-log', {
      page: params.page || 1,
      per_page: params.per_page || 20,
    });
  },

  // Enable two-factor authentication
  enableTwoFactor: async (): Promise<{
    qr_code: string;
    backup_codes: string[];
    secret: string;
  }> => {
    return apiService.post('/auth/2fa/enable');
  },

  // Confirm two-factor authentication setup
  confirmTwoFactor: async (token: string): Promise<BaseResponse<any>> => {
    return apiService.post('/auth/2fa/confirm', { token });
  },

  // Disable two-factor authentication
  disableTwoFactor: async (token: string): Promise<BaseResponse<any>> => {
    return apiService.post('/auth/2fa/disable', { token });
  },

  // Generate new backup codes
  generateBackupCodes: async (): Promise<{ backup_codes: string[] }> => {
    return apiService.post('/auth/2fa/backup-codes');
  },

  // Check authentication status
  checkAuth: async (): Promise<boolean> => {
    try {
      await authService.getCurrentUser();
      return true;
    } catch (error) {
      clearTokens();
      return false;
    }
  },

  // Social login (Google, LinkedIn, etc.)
  socialLogin: async (provider: 'google' | 'linkedin', token: string): Promise<AuthResponse> => {
    const response = await apiService.post<AuthResponse>(`/auth/social/${provider}`, { token });
    setTokens({
      access_token: response.access_token,
      refresh_token: response.refresh_token,
    });
    return response;
  },

  // Link social account
  linkSocialAccount: async (provider: 'google' | 'linkedin', token: string): Promise<BaseResponse<any>> => {
    return apiService.post<BaseResponse<any>>(`/auth/social/${provider}/link`, { token });
  },

  // Unlink social account
  unlinkSocialAccount: async (provider: 'google' | 'linkedin'): Promise<BaseResponse<any>> => {
    return apiService.delete<BaseResponse<any>>(`/auth/social/${provider}/unlink`);
  },

  // Get linked social accounts
  getLinkedAccounts: async (): Promise<Array<{
    provider: string;
    email: string;
    linked_at: string;
  }>> => {
    return apiService.get('/auth/social/linked');
  },
};