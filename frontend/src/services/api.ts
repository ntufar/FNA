/**
 * API Client for FNA Platform
 * 
 * Provides a centralized HTTP client for communicating with the backend API.
 * Handles authentication, error responses, and request/response transformations.
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { toast } from 'react-toastify';

// API Response Types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  request_id?: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details: Record<string, any>;
  };
  request_id?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Authentication Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  company_name?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface User {
  id: string;
  email: string;
  subscription_tier: 'Basic' | 'Pro' | 'Enterprise';
  created_at: string;
  last_login: string;
  is_active: boolean;
}

// Company Types
export interface Company {
  id: string;
  ticker_symbol: string;
  company_name: string;
  sector?: string;
  industry?: string;
  created_at: string;
  updated_at: string;
}

// Trends Types (US3)
export interface CompanyTrendPoint {
  date_label: string; // e.g. "Q1 2025" or ISO date
  optimism: number; // 0..1
  risk: number; // 0..1
  uncertainty: number; // 0..1
}

export interface CreateCompanyRequest {
  ticker_symbol: string;
  company_name: string;
  sector?: string;
  industry?: string;
}

// Report Types
export interface FinancialReport {
  id: string;
  company_id: string;
  company_name?: string; // provided by backend list endpoint
  ticker_symbol?: string; // provided by backend list endpoint
  report_type: '10-K' | '10-Q' | '8-K' | 'Annual' | 'Other';
  fiscal_period: string;
  filing_date: string;
  report_url?: string;
  file_path: string;
  file_format: 'PDF' | 'HTML' | 'TXT' | 'iXBRL';
  file_size_bytes: number;
  download_source: 'SEC_AUTO' | 'MANUAL_UPLOAD';
  processing_status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  created_at: string;
  processed_at?: string;
  company?: Company;
}

export interface UploadReportRequest {
  company_id: string;
  report_type: string;
  fiscal_period?: string;
  file: File;
}

export interface DownloadReportRequest {
  ticker_symbol: string;
  report_type: string;
  year?: number;
  accession_number?: string;
  filing_date?: string;
}

export interface AvailableFiling {
  accession_number: string;
  filing_date: string;
  fiscal_period: string | null;
  report_type: string;
  is_downloaded: boolean;
  existing_report_id?: string | null;
  file_format: string;
  report_url?: string | null;
}

export interface ReportUploadResponse {
  report_id: string;
  message: string;
  processing_status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  file_path?: string;
  estimated_processing_time?: string;
}

// Analysis Types
export interface ThemeObject { term: string; weight?: number }
export interface RiskIndicatorObject { type?: string; severity?: string; detail?: string; term?: string; weight?: number; [k: string]: any }

export interface NarrativeAnalysis {
  id: string;
  report_id: string;
  optimism_score: number;
  optimism_confidence: number;
  risk_score: number;
  risk_confidence: number;
  uncertainty_score: number;
  uncertainty_confidence: number;
  key_themes: Array<string | ThemeObject>;
  risk_indicators: Array<string | RiskIndicatorObject>;
  narrative_sections: Record<string, string>;
  financial_metrics?: Record<string, any>;
  processing_time_seconds: number;
  model_version: string;
  created_at: string;
  report?: FinancialReport;
}

export interface ComparisonAnalysis {
  id: string;
  company_id: string;
  base_analysis_id: string;
  comparison_analysis_id: string;
  optimism_delta: number;
  risk_delta: number;
  uncertainty_delta: number;
  overall_sentiment_delta: number;
  themes_added: string[];
  themes_removed: string[];
  themes_evolved: Record<string, any>;
  shift_significance: 'MINOR' | 'MODERATE' | 'MAJOR' | 'CRITICAL';
  created_at: string;
  base_analysis?: NarrativeAnalysis;
  comparison_analysis?: NarrativeAnalysis;
}

// Alert Types
export interface Alert {
  id: string;
  user_id: string;
  company_id: string;
  delta_id: string;
  alert_type: 'SENTIMENT_SHIFT' | 'RISK_INCREASE' | 'THEME_CHANGE';
  threshold_percentage: number;
  actual_change_percentage: number;
  alert_message: string;
  is_read: boolean;
  delivery_method: 'IN_APP' | 'EMAIL' | 'WEBHOOK';
  created_at: string;
  delivered_at?: string;
  company?: Company;
}

// Configuration
const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8001/v1';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load tokens from localStorage
    this.loadTokens();

    // Request interceptor for authentication
    this.client.interceptors.request.use(
      (config) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling and token refresh
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        // Handle 401 errors with token refresh
        if (error.response?.status === 401 && !originalRequest._retry && this.refreshToken) {
          originalRequest._retry = true;

          try {
            await this.refreshAccessToken();
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${this.accessToken}`;
            }
            return this.client(originalRequest);
          } catch (refreshError) {
            this.logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        // Handle other errors
        this.handleApiError(error);
        return Promise.reject(error);
      }
    );
  }

  private loadTokens(): void {
    this.accessToken = localStorage.getItem('fna_access_token');
    this.refreshToken = localStorage.getItem('fna_refresh_token');
  }

  private saveTokens(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    localStorage.setItem('fna_access_token', accessToken);
    localStorage.setItem('fna_refresh_token', refreshToken);
  }

  private clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('fna_access_token');
    localStorage.removeItem('fna_refresh_token');
    localStorage.removeItem('fna_user');
  }

  private handleApiError(error: AxiosError<ApiError>): void {
    const errorData = error.response?.data;
    const errorMessage = errorData?.error?.message || error.message || 'An unexpected error occurred';

    // Show toast notification for user-facing errors
    if (error.response?.status && error.response.status >= 400 && error.response.status < 500) {
      toast.error(errorMessage);
    } else if (error.response?.status && error.response.status >= 500) {
      toast.error('Server error. Please try again later.');
    } else if (error.code === 'NETWORK_ERROR') {
      toast.error('Network error. Please check your connection.');
    }

    console.error('API Error:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: errorData,
      url: error.config?.url,
      method: error.config?.method,
    });
  }

  // Authentication Methods
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/login', credentials);
    const authData = response.data;
    
    this.saveTokens(authData.access_token, authData.refresh_token);
    localStorage.setItem('fna_user', JSON.stringify(authData.user));
    
    return authData;
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/register', userData);
    const authData = response.data;
    
    this.saveTokens(authData.access_token, authData.refresh_token);
    localStorage.setItem('fna_user', JSON.stringify(authData.user));
    
    return authData;
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearTokens();
    }
  }

  async refreshAccessToken(): Promise<void> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await this.client.post<AuthResponse>('/auth/refresh', {
      refresh_token: this.refreshToken,
    });

    const authData = response.data;
    this.saveTokens(authData.access_token, authData.refresh_token);
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me');
    const user = response.data;
    localStorage.setItem('fna_user', JSON.stringify(user));
    return user;
  }

  // Company Methods
  async getCompanies(): Promise<Company[]> {
    const response = await this.client.get<Company[]>('/companies');
    return response.data;
  }

  async getCompany(id: string): Promise<Company> {
    const response = await this.client.get<Company>(`/companies/${id}`);
    return response.data;
  }

  async createCompany(companyData: CreateCompanyRequest): Promise<Company> {
    const response = await this.client.post<Company>('/companies', companyData);
    return response.data;
  }

  async updateCompany(id: string, companyData: Partial<CreateCompanyRequest>): Promise<Company> {
    const response = await this.client.put<Company>(`/companies/${id}`, companyData);
    return response.data;
  }

  async deleteCompany(id: string): Promise<void> {
    await this.client.delete(`/companies/${id}`);
  }

  async getCompanyReports(id: string): Promise<FinancialReport[]> {
    const response = await this.client.get<FinancialReport[]>(`/companies/${id}/reports`);
    return response.data;
  }

  async getCompanyTrends(id: string): Promise<CompanyTrendPoint[]> {
    const response = await this.client.get(`/companies/${id}/trends`);
    const body: any = response.data;
    // Backend returns shape: { company: {...}, timeline: [{ date, optimism, risk, uncertainty }], ... }
    if (Array.isArray(body?.timeline)) {
      return (body.timeline as any[]).map((p) => ({
        date_label: p.date || '',
        optimism: typeof p.optimism === 'number' ? p.optimism : null,
        risk: typeof p.risk === 'number' ? p.risk : null,
        uncertainty: typeof p.uncertainty === 'number' ? p.uncertainty : null,
      })) as CompanyTrendPoint[];
    }
    if (Array.isArray(body)) return body as CompanyTrendPoint[];
    if (Array.isArray(body?.data)) return body.data as CompanyTrendPoint[];
    return [];
  }

  // Report Methods
  async uploadReport(reportData: UploadReportRequest): Promise<ReportUploadResponse> {
    const formData = new FormData();
    formData.append('file', reportData.file);
    formData.append('company_id', reportData.company_id);
    formData.append('report_type', reportData.report_type);
    if (reportData.fiscal_period) {
      formData.append('fiscal_period', reportData.fiscal_period);
    }

    const response = await this.client.post<ReportUploadResponse>('/reports/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async downloadReport(downloadData: DownloadReportRequest): Promise<ReportUploadResponse> {
    const response = await this.client.post<ReportUploadResponse>('/reports/download', downloadData);
    return response.data;
  }

  async getAvailableFilings(
    tickerSymbol: string,
    reportType: string,
    fiscalYear?: number
  ): Promise<AvailableFiling[]> {
    const params: any = { ticker_symbol: tickerSymbol, report_type: reportType };
    if (fiscalYear) {
      params.fiscal_year = fiscalYear;
    }
    const response = await this.client.get<AvailableFiling[]>('/reports/available-filings', { params });
    return response.data;
  }

  async getReport(id: string): Promise<FinancialReport> {
    const response = await this.client.get<FinancialReport>(`/reports/${id}`);
    return response.data;
  }

  async getReports(params?: { company_id?: string; report_type?: string; status?: string; skip?: number; limit?: number }): Promise<FinancialReport[]> {
    const response = await this.client.get<FinancialReport[]>('/reports', { params });
    return response.data;
  }

  async deleteReport(id: string): Promise<void> {
    await this.client.delete(`/reports/${id}`);
  }

  async setReportStatus(id: string, status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'): Promise<FinancialReport> {
    const response = await this.client.patch<FinancialReport>(`/reports/${id}/status`, { status });
    return response.data as any;
  }

  // Analysis Methods
  async getReportAnalysis(reportId: string): Promise<NarrativeAnalysis> {
    const response = await this.client.get<NarrativeAnalysis>(`/reports/${reportId}/analysis`);
    return response.data;
  }

  async getAnalyses(params?: { report_id?: string; company_id?: string; skip?: number; limit?: number }): Promise<NarrativeAnalysis[]> {
    const response = await this.client.get<NarrativeAnalysis[]>('/analysis', { params });
    return response.data as any; // backend may return partial fields in dev; cast for now
  }

  async getAnalysis(analysisId: string): Promise<NarrativeAnalysis> {
    const response = await this.client.get<NarrativeAnalysis>(`/analysis/${analysisId}`);
    return response.data as any;
  }

  async waitForReportAnalysis(
    reportId: string,
    options: { pollIntervalMs?: number; timeoutMs?: number } = {}
  ): Promise<NarrativeAnalysis> {
    const pollIntervalMs = options.pollIntervalMs ?? 3000;
    const timeoutMs = options.timeoutMs ?? 60000;
    const start = Date.now();

    /* eslint-disable no-constant-condition */
    while (true) {
      const response = await this.client.get<NarrativeAnalysis | { detail?: string }>(`/reports/${reportId}/analysis`, {
        validateStatus: () => true,
      });

      if (response.status === 200) {
        return response.data as NarrativeAnalysis;
      }

      if (response.status === 202) {
        if (Date.now() - start >= timeoutMs) {
          throw new Error('Analysis is still processing. Please try again later.');
        }
        await new Promise((r) => setTimeout(r, pollIntervalMs));
        continue;
      }

      // Other statuses: surface error via generic handler
      const err = new Error((response.data as any)?.detail || 'Failed to fetch analysis');
      throw err;
    }
  }

  async triggerAnalysis(reportId: string): Promise<NarrativeAnalysis> {
    const response = await this.client.post<NarrativeAnalysis>(`/reports/${reportId}/analyze`);
    return response.data;
  }

  async compareAnalyses(baseAnalysisId: string, comparisonAnalysisId: string): Promise<ComparisonAnalysis> {
    const response = await this.client.post<ComparisonAnalysis>('/analysis/compare', {
      base_analysis_id: baseAnalysisId,
      comparison_analysis_id: comparisonAnalysisId,
    });
    return response.data;
  }

  async getComparison(id: string): Promise<ComparisonAnalysis> {
    const response = await this.client.get<ComparisonAnalysis>(`/analysis/comparisons/${id}`);
    return response.data;
  }

  async searchSimilarNarratives(query: string, limit: number = 10): Promise<NarrativeAnalysis[]> {
    const response = await this.client.post<NarrativeAnalysis[]>('/analysis/search', {
      query,
      limit,
    });
    return response.data;
  }

  // Alert Methods
  async getAlerts(): Promise<Alert[]> {
    const response = await this.client.get<Alert[]>('/alerts');
    return response.data;
  }

  async markAlertAsRead(id: string): Promise<Alert> {
    const response = await this.client.patch<Alert>(`/alerts/${id}/read`);
    return response.data;
  }

  async createAlertPreference(companyId: string, alertType: string, threshold: number): Promise<void> {
    await this.client.post('/alerts/preferences', {
      company_id: companyId,
      alert_type: alertType,
      threshold_percentage: threshold,
    });
  }

  // Utility Methods
  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  getCurrentUserFromStorage(): User | null {
    const userString = localStorage.getItem('fna_user');
    return userString ? JSON.parse(userString) : null;
  }

  async healthCheck(): Promise<Record<string, any>> {
    const response = await this.client.get('/health', {
      headers: {
        Authorization: '', // Remove auth for health check
      },
    });
    return response.data;
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export for direct use
export default apiClient;
