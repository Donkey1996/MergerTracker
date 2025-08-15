export interface User {
  user_id: string;
  email: string;
  first_name: string;
  last_name: string;
  company?: string;
  job_title?: string;
  subscription_tier: 'Free' | 'Professional' | 'Enterprise';
  subscription_expires_at?: string;
  preferences: UserPreferences;
  created_at: string;
  last_login_at?: string;
  is_active: boolean;
  is_verified: boolean;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  email_notifications: boolean;
  deal_alerts: boolean;
  news_digest_frequency: 'daily' | 'weekly' | 'monthly' | 'never';
  preferred_industries: string[];
  preferred_regions: string[];
  dashboard_layout: 'compact' | 'detailed';
  currency_preference: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  company?: string;
  job_title?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface TokenRefreshRequest {
  refresh_token: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateProfile: (updates: Partial<User>) => Promise<void>;
  changePassword: (request: ChangePasswordRequest) => Promise<void>;
}