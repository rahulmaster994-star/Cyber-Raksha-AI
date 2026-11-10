/**
 * Cyber Raksha AI - Centralized API Service
 * Handles live communication with the FastAPI backend.
 */

export interface RootInfo {
  name: string;
  version: string;
  status: string;
  stage: string;
  docs_url: string;
  health_url: string;
  system_info_url: string;
}

export interface HealthCheckData {
  status: string;
  application: string;
  version: string;
  stage: string;
  database_connected: boolean;
  database_latency_ms: number;
  database_message: string;
  uptime_seconds: number;
  timestamp: string;
}

export interface SecurityModule {
  id: string;
  name: string;
  code: string;
  category: string;
  status: string;
  is_implemented: boolean;
  description: string;
  planned_capabilities: string[];
  stage_planned: string;
}

export interface SecurityModulesResponse {
  total_modules: number;
  implemented_count: number;
  planned_count: number;
  modules: SecurityModule[];
}

export interface SystemInfoData {
  application_name: string;
  version: string;
  development_stage: string;
  environment: string;
  backend_status: string;
  database_status: {
    connected: boolean;
    dialect: string;
    latency_ms: number;
    message: string;
    storage: string;
  };
  ai_engine_status: {
    stage: string;
    loaded_models_count: number;
    active_inference_workers: number;
    engine_status: string;
    notes: string;
  };
  implemented_components: string[];
  planned_components: string[];
  system_architecture: {
    frontend: string;
    backend: string;
    database_orm: string;
    ai_subsystem: string;
    cors_enabled: boolean;
  };
  timestamp: string;
}

export interface UnifiedRiskEvidenceItem {
  type: string;
  description: string;
  risk_contribution: number;
}

export interface UnifiedRiskEvaluationResponse {
  indicator: string;
  indicator_type: string;
  risk_level: 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_score: number;
  confidence_score: number;
  fraud_category?: string;
  detection_reasons: string[];
  corroborating_sources: string[];
  is_verified_threat: boolean;
  recommended_action: string;
  incident_id?: number | null;
  evaluated_at: string;
  classification?: string;
  intelligence_status?: string;
  evidence_items?: UnifiedRiskEvidenceItem[];
}

export interface BrandImpersonationDetail {
  brand_id: string;
  brand_name: string;
  category: string;
  matched_keyword: string;
  impersonation_type: string;
  risk_contribution: number;
  description: string;
}

export interface URLAnalysisDetail {
  features: Record<string, any>;
  risk_indicators: string[];
  latency_ms?: number;
  ml_probabilities?: {
    phishing: number;
    legitimate: number;
  };
  model_algorithm?: string;
  feature_count?: number;
  brand_impersonation?: BrandImpersonationDetail;
}

export interface URLDetectionResponse {
  success: boolean;
  url?: string;
  classification: 'LEGITIMATE' | 'PHISHING' | 'SUSPICIOUS' | 'INCONCLUSIVE' | 'INVALID' | 'ERROR';
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'UNKNOWN';
  risk_score: number;
  model_version: string;
  confidence?: number;
  analysis: URLAnalysisDetail;
  recommendation: string;
}

export interface DetectionStatusResponse {
  model_available: boolean;
  model_loaded: boolean;
  model_version: string;
  algorithm: string;
  training_status: string;
  engine_stage: string;
  dataset_status: string;
  inference_status: string;
  metrics_summary?: Record<string, any>;
}

export interface AnalysisHistoryItem {
  id: number;
  module_code: string;
  target_identifier: string;
  status: string;
  risk_score?: number;
  threat_category?: string;
  summary?: string;
  explanation?: string;
  created_at: string;
}

export interface AnalysisHistoryResponse {
  total_records: number;
  records: AnalysisHistoryItem[];
}

export interface NotificationItem {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  category: string;
  target_domain?: string | null;
  recommended_action?: string | null;
  source_component: string;
  metadata_json?: string | null;
  is_read: boolean;
  recipient_role: string;
  created_at: string;
}

export interface NotificationListResponse {
  total: number;
  unread_count: number;
  items: NotificationItem[];
}

export interface NotificationPreferenceData {
  user_id: string;
  browser_notifications_enabled: boolean;
  min_severity: string;
  categories_enabled: string[];
  sound_enabled: boolean;
  updated_at: string;
}

export interface CommunicationAnalysisDetail {
  latency_ms?: number;
  model_algorithm?: string;
  ml_fraud_probability?: number;
  indicators_breakdown?: {
    urgency_markers: number;
    financial_markers: number;
    impersonation_markers: number;
    social_engineering_markers: number;
    digital_arrest_markers: number;
  };
  is_digital_arrest_candidate?: boolean;
}

export interface CommunicationAnalyzeResponse {
  success: boolean;
  classification: 'DIGITAL_ARREST_SCAM' | 'FINANCIAL_SCAM' | 'IMPERSONATION' | 'PHISHING' | 'SUSPICIOUS' | 'SAFE' | 'INCONCLUSIVE' | 'INVALID';
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'UNKNOWN';
  risk_score: number;
  confidence?: number;
  detected_indicators: string[];
  explanation: string;
  recommendations: string[];
  model_version: string;
  analysis?: CommunicationAnalysisDetail;
}

export interface CommunicationStatusResponse {
  model_available: boolean;
  model_loaded: boolean;
  model_version: string;
  algorithm: string;
  engine_stage: string;
  training_status: string;
  inference_status: string;
  metrics_summary?: Record<string, any>;
}

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  isOnline: boolean;
}

import type {
  AudioMetadata,
  AudioIndicator,
  AudioAnalysisResponse,
  AudioStatusResponse,
} from './audio_types';

import type {
  ThreatIndicator,
  ThreatSearchResponse,
  ThreatIntelStatusResponse,
  UnifiedAnalyzeResponse,
  LiveThreatEvent,
} from './intel_types';

import type {
  IncidentAction,
  SecurityIncident,
  IncidentListResponse,
  ProtectionOverviewResponse,
  AssistantGuidanceResponse,
  ResponsePlaybook,
} from './prevention_types';

export type {
  AudioMetadata,
  AudioIndicator,
  AudioAnalysisResponse,
  AudioStatusResponse,
  ThreatIndicator,
  ThreatSearchResponse,
  ThreatIntelStatusResponse,
  UnifiedAnalyzeResponse,
  LiveThreatEvent,
  IncidentAction,
  SecurityIncident,
  IncidentListResponse,
  ProtectionOverviewResponse,
  AssistantGuidanceResponse,
  ResponsePlaybook,
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  private async request<T>(endpoint: string): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        return {
          data: null,
          error: `HTTP Error ${response.status}: ${response.statusText}`,
          isOnline: true,
        };
      }

      const data = await response.json();
      return {
        data,
        error: null,
        isOnline: true,
      };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Connection failed';
      return {
        data: null,
        error: `Backend unreachable at ${this.baseUrl} (${message})`,
        isOnline: false,
      };
    }
  }

  public async getRoot(): Promise<ApiResponse<RootInfo>> {
    return this.request<RootInfo>('/');
  }

  public async getHealth(): Promise<ApiResponse<HealthCheckData>> {
    return this.request<HealthCheckData>('/api/health');
  }

  public async getSystemInfo(): Promise<ApiResponse<SystemInfoData>> {
    return this.request<SystemInfoData>('/api/system/info');
  }

  public async getDashboardStats(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/system/dashboard-stats');
  }

  public async getPrivacyPolicy(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/privacy/policy');
  }

  public async getPrivacySettings(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/privacy/settings');
  }

  public async updatePrivacySettings(data: any): Promise<ApiResponse<any>> {
    const fullUrl = `${this.baseUrl}/api/v1/privacy/settings`;
    try {
      const response = await fetch(fullUrl, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const resData = await response.json();
      return { data: resData, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async purgeAnalysisHistory(moduleCode?: string): Promise<ApiResponse<any>> {
    const q = moduleCode ? `?module_code=${encodeURIComponent(moduleCode)}` : '';
    const fullUrl = `${this.baseUrl}/api/v1/privacy/history${q}`;
    try {
      const response = await fetch(fullUrl, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
      });
      const resData = await response.json();
      return { data: resData, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async getModules(): Promise<ApiResponse<SecurityModulesResponse>> {
    return this.request<SecurityModulesResponse>('/api/modules');
  }

  public async detectUrl(url: string): Promise<ApiResponse<URLDetectionResponse>> {
    const fullUrl = `${this.baseUrl}/api/v1/detection/url`;
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        const detail = errorBody?.detail || `HTTP Error ${response.status}: ${response.statusText}`;
        return {
          data: null,
          error: detail,
          isOnline: true,
        };
      }

      const data = await response.json();
      return {
        data,
        error: null,
        isOnline: true,
      };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Request failed';
      return {
        data: null,
        error: `Could not reach detection API (${message})`,
        isOnline: false,
      };
    }
  }

  public async getDetectionStatus(): Promise<ApiResponse<DetectionStatusResponse>> {
    return this.request<DetectionStatusResponse>('/api/v1/detection/status');
  }

  public async getDetectionHistory(limit = 20): Promise<ApiResponse<AnalysisHistoryResponse>> {
    return this.request<AnalysisHistoryResponse>(`/api/v1/detection/history?limit=${limit}`);
  }

  public async analyzeCommunication(
    message: string,
    isDigitalArrest = false
  ): Promise<ApiResponse<CommunicationAnalyzeResponse>> {
    const endpoint = isDigitalArrest
      ? '/api/v1/communication/digital-arrest/analyze'
      : '/api/v1/communication/analyze';
    const fullUrl = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        const detail = errorBody?.detail || `HTTP Error ${response.status}: ${response.statusText}`;
        return {
          data: null,
          error: detail,
          isOnline: true,
        };
      }

      const data = await response.json();
      return {
        data,
        error: null,
        isOnline: true,
      };
    } catch (err: unknown) {
      const message_str = err instanceof Error ? err.message : 'Request failed';
      return {
        data: null,
        error: `Could not reach communication API (${message_str})`,
        isOnline: false,
      };
    }
  }

  public async getCommunicationStatus(): Promise<ApiResponse<CommunicationStatusResponse>> {
    return this.request<CommunicationStatusResponse>('/api/v1/communication/status');
  }

  public async getCommunicationHistory(limit = 20): Promise<ApiResponse<AnalysisHistoryResponse>> {
    return this.request<AnalysisHistoryResponse>(`/api/v1/communication/history?limit=${limit}`);
  }

  public async analyzeAudio(file: File): Promise<ApiResponse<AudioAnalysisResponse>> {
    const fullUrl = `${this.baseUrl}/api/v1/audio/analyze`;
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        body: formData,
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        const detail = errorBody?.detail || `HTTP Error ${response.status}: ${response.statusText}`;
        return {
          data: null,
          error: detail,
          isOnline: true,
        };
      }

      const data = await response.json();
      return {
        data,
        error: null,
        isOnline: true,
      };
    } catch (err: unknown) {
      const message_str = err instanceof Error ? err.message : 'Upload failed';
      return {
        data: null,
        error: `Could not reach audio analysis API (${message_str})`,
        isOnline: false,
      };
    }
  }

  public async getAudioStatus(): Promise<ApiResponse<AudioStatusResponse>> {
    return this.request<AudioStatusResponse>('/api/v1/audio/status');
  }

  public async getAudioHistory(limit = 20): Promise<ApiResponse<AnalysisHistoryResponse>> {
    return this.request<AnalysisHistoryResponse>(`/api/v1/audio/history?limit=${limit}`);
  }

  // Stage 5: Threat Intelligence & Unified Risk Engine
  public async getIntelStatus(): Promise<ApiResponse<ThreatIntelStatusResponse>> {
    return this.request<ThreatIntelStatusResponse>('/api/v1/intel/status');
  }

  public async searchThreatIndicator(query: string, indicator_type?: string): Promise<ApiResponse<ThreatSearchResponse>> {
    const fullUrl = `${this.baseUrl}/api/v1/intel/search`;
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, indicator_type }),
      });
      if (!response.ok) {
        return { data: null, error: `HTTP ${response.status}`, isOnline: true };
      }
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async getVerifiedIndicators(limit = 50): Promise<ApiResponse<ThreatIndicator[]>> {
    return this.request<ThreatIndicator[]>(`/api/v1/intel/indicators?limit=${limit}`);
  }

  public async triggerFeedUpdate(): Promise<ApiResponse<any>> {
    const fullUrl = `${this.baseUrl}/api/v1/intel/feed/update`;
    try {
      const response = await fetch(fullUrl, { method: 'POST' });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async analyzeUnified(params: {
    url?: string;
    message?: string;
    is_digital_arrest?: boolean;
  }): Promise<ApiResponse<UnifiedAnalyzeResponse>> {
    const fullUrl = `${this.baseUrl}/api/v1/intel/unified/analyze`;
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => null);
        return { data: null, error: err?.detail || `HTTP ${response.status}`, isOnline: true };
      }
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async getLiveEvents(limit = 20): Promise<ApiResponse<LiveThreatEvent[]>> {
    return this.request<LiveThreatEvent[]>(`/api/v1/intel/events/live?limit=${limit}`);
  }

  // Stage 6: Proactive Prevention & Incident Response
  public async getProtectionOverview(): Promise<ApiResponse<ProtectionOverviewResponse>> {
    return this.request<ProtectionOverviewResponse>('/api/v1/protection/overview');
  }

  public async getIncidents(status?: string): Promise<ApiResponse<IncidentListResponse>> {
    const url = status ? `/api/v1/incidents?status=${status}` : '/api/v1/incidents';
    return this.request<IncidentListResponse>(url);
  }

  public async getIncidentById(id: number): Promise<ApiResponse<SecurityIncident>> {
    return this.request<SecurityIncident>(`/api/v1/incidents/${id}`);
  }

  public async createIncident(data: {
    category: string;
    title: string;
    severity?: string;
    summary: string;
    related_analysis_id?: number;
    evidence_references?: string;
  }): Promise<ApiResponse<SecurityIncident>> {
    const fullUrl = `${this.baseUrl}/api/v1/incidents`;
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        return { data: null, error: `HTTP ${response.status}`, isOnline: true };
      }
      const resData = await response.json();
      return { data: resData, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async completeIncidentAction(actionId: number): Promise<ApiResponse<IncidentAction>> {
    const fullUrl = `${this.baseUrl}/api/v1/prevention/actions/${actionId}/complete`;
    try {
      const response = await fetch(fullUrl, { method: 'POST' });
      const resData = await response.json();
      return { data: resData, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async updateIncidentStatus(id: number, status: string, notes?: string): Promise<ApiResponse<SecurityIncident>> {
    const fullUrl = `${this.baseUrl}/api/v1/incidents/${id}`;
    try {
      const response = await fetch(fullUrl, {
        method: 'PATCH',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status, resolution_notes: notes }),
      });
      const resData = await response.json();
      return { data: resData, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async askAssistant(query: string): Promise<ApiResponse<AssistantGuidanceResponse>> {
    const fullUrl = `${this.baseUrl}/api/v1/assistant/security-guidance`;
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      const resData = await response.json();
      return { data: resData, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async getPlaybooks(): Promise<ApiResponse<ResponsePlaybook[]>> {
    return this.request<ResponsePlaybook[]>('/api/v1/prevention/playbooks');
  }

  // --- Stage 9 Observability & Admin Methods ---

  public async getDetailedHealth(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/monitoring/health/detailed');
  }

  public async getPerformanceMetrics(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/monitoring/metrics');
  }

  public async getFeedHealth(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/monitoring/feeds');
  }

  public async getModelsOverview(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/monitoring/models');
  }

  public async getModelDrift(modelId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/monitoring/models/${modelId}/drift`);
  }

  public async submitFeedback(payload: {
    analysis_id?: number;
    target_identifier?: string;
    feedback_category: string;
    user_explanation?: string;
    user_provided_label?: string;
  }): Promise<ApiResponse<any>> {
    const fullUrl = `${this.baseUrl}/api/v1/feedback/submit`;
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        return { data: null, error: data.detail || 'Feedback submission failed', isOnline: true };
      }
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async getAdminOverview(adminKey: string): Promise<ApiResponse<any>> {
    const fullUrl = `${this.baseUrl}/api/v1/admin/overview`;
    try {
      const response = await fetch(fullUrl, {
        headers: {
          'Accept': 'application/json',
          'X-Admin-Key': adminKey,
        },
      });
      const data = await response.json();
      if (!response.ok) {
        return { data: null, error: data.message || 'Unauthorized or failed', isOnline: true };
      }
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async getFeatureFlags(adminKey: string): Promise<ApiResponse<any>> {
    const fullUrl = `${this.baseUrl}/api/v1/admin/feature-flags`;
    try {
      const response = await fetch(fullUrl, {
        headers: {
          'Accept': 'application/json',
          'X-Admin-Key': adminKey,
        },
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async updateFeatureFlag(adminKey: string, flagName: string, enabled: boolean): Promise<ApiResponse<any>> {
    const fullUrl = `${this.baseUrl}/api/v1/admin/feature-flags/${flagName}`;
    try {
      const response = await fetch(fullUrl, {
        method: 'PATCH',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-Admin-Key': adminKey,
        },
        body: JSON.stringify({ enabled }),
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async getPendingFeedback(adminKey: string): Promise<ApiResponse<any>> {
    const fullUrl = `${this.baseUrl}/api/v1/admin/feedback/pending`;
    try {
      const response = await fetch(fullUrl, {
        headers: {
          'Accept': 'application/json',
          'X-Admin-Key': adminKey,
        },
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async reviewFeedback(adminKey: string, feedbackId: number, status: string, notes?: string, reviewer?: string): Promise<ApiResponse<any>> {
    const fullUrl = `${this.baseUrl}/api/v1/admin/feedback/${feedbackId}/review`;
    try {
      const response = await fetch(fullUrl, {
        method: 'PATCH',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-Admin-Key': adminKey,
        },
        body: JSON.stringify({
          review_status: status,
          reviewer_notes: notes,
          reviewed_by: reviewer || 'admin_operator',
        }),
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async getAdminAlerts(adminKey: string): Promise<ApiResponse<any>> {
    const fullUrl = `${this.baseUrl}/api/v1/admin/alerts`;
    try {
      const response = await fetch(fullUrl, {
        headers: {
          'Accept': 'application/json',
          'X-Admin-Key': adminKey,
        },
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async clearAlerts(adminKey: string): Promise<ApiResponse<any>> {
    const fullUrl = `${this.baseUrl}/api/v1/admin/alerts/clear`;
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'X-Admin-Key': adminKey,
        },
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  // ---------------------------------------------------------------------------
  // Phase A3: Security Notifications & Real-Time Alerts
  // ---------------------------------------------------------------------------

  public async getNotifications(params?: {
    limit?: number;
    offset?: number;
    is_read?: boolean;
    severity?: string;
    category?: string;
  }): Promise<ApiResponse<NotificationListResponse>> {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());
    if (params?.is_read !== undefined) query.set('is_read', params.is_read.toString());
    if (params?.severity) query.set('severity', params.severity);
    if (params?.category) query.set('category', params.category);

    const endpoint = `/api/v1/notifications?${query.toString()}`;
    return this.request<NotificationListResponse>(endpoint);
  }

  public async getUnreadNotificationCount(): Promise<ApiResponse<{ unread_count: number }>> {
    return this.request<{ unread_count: number }>('/api/v1/notifications/unread-count');
  }

  public async markNotificationRead(id: number): Promise<ApiResponse<NotificationItem>> {
    const fullUrl = `${this.baseUrl}/api/v1/notifications/${id}/read`;
    try {
      const response = await fetch(fullUrl, {
        method: 'PATCH',
        headers: { 'Accept': 'application/json' },
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async markAllNotificationsRead(): Promise<ApiResponse<{ status: string; marked_read_count: number }>> {
    const fullUrl = `${this.baseUrl}/api/v1/notifications/read-all`;
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: { 'Accept': 'application/json' },
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async deleteNotification(id: number): Promise<ApiResponse<{ status: string }>> {
    const fullUrl = `${this.baseUrl}/api/v1/notifications/${id}`;
    try {
      const response = await fetch(fullUrl, {
        method: 'DELETE',
        headers: { 'Accept': 'application/json' },
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async clearAllNotifications(): Promise<ApiResponse<{ status: string; cleared_count: number }>> {
    const fullUrl = `${this.baseUrl}/api/v1/notifications`;
    try {
      const response = await fetch(fullUrl, {
        method: 'DELETE',
        headers: { 'Accept': 'application/json' },
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async getNotificationPreferences(): Promise<ApiResponse<NotificationPreferenceData>> {
    return this.request<NotificationPreferenceData>('/api/v1/notifications/preferences');
  }

  public async updateNotificationPreferences(
    prefs: Partial<NotificationPreferenceData>
  ): Promise<ApiResponse<NotificationPreferenceData>> {
    const fullUrl = `${this.baseUrl}/api/v1/notifications/preferences`;
    try {
      const response = await fetch(fullUrl, {
        method: 'PUT',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(prefs),
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public subscribeNotificationStream(
    onNotification: (item: NotificationItem) => void,
    onConnected?: () => void
  ): () => void {
    const fullUrl = `${this.baseUrl}/api/v1/notifications/stream`;
    let eventSource: EventSource | null = null;
    try {
      eventSource = new EventSource(fullUrl);
      eventSource.addEventListener('connected', () => {
        if (onConnected) onConnected();
      });
      eventSource.addEventListener('notification', (event) => {
        try {
          const item = JSON.parse(event.data);
          onNotification(item);
        } catch (_) {}
      });
    } catch (_) {}

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }

  // ── Phase B3: Unified Protection Dashboard & Security APIs ─────────────────

  public async getDashboardOverview(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/dashboard/overview');
  }

  public async getDashboardActivity(limit: number = 25): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/dashboard/activity?limit=${limit}`);
  }

  public async getDashboardIncidents(limit: number = 10): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/dashboard/incidents?limit=${limit}`);
  }

  public async evaluateUnifiedRisk(indicator: string, indicatorType: string, source: string = 'FRONTEND_DASHBOARD'): Promise<ApiResponse<UnifiedRiskEvaluationResponse>> {
    const fullUrl = `${this.baseUrl}/api/v1/security/risk/evaluate`;
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          indicator,
          indicator_type: indicatorType,
          source_component: source,
        }),
      });
      const data: UnifiedRiskEvaluationResponse = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async acknowledgeIncident(incidentId: number): Promise<ApiResponse<any>> {
    const fullUrl = `${this.baseUrl}/api/v1/incidents/${incidentId}/acknowledge`;
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: { 'Accept': 'application/json' },
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public async resolveIncident(incidentId: number, resolutionNotes: string = 'Resolved via Security Dashboard'): Promise<ApiResponse<any>> {
    const fullUrl = `${this.baseUrl}/api/v1/incidents/${incidentId}/resolve`;
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resolution_notes: resolutionNotes,
          close_incident: true,
        }),
      });
      const data = await response.json();
      return { data, error: null, isOnline: true };
    } catch (e: any) {
      return { data: null, error: e.message, isOnline: false };
    }
  }

  public subscribeSecurityStream(
    onMessage: (event: any) => void,
    onConnected?: () => void
  ): () => void {
    const fullUrl = `${this.baseUrl}/api/v1/security/stream`;
    let eventSource: EventSource | null = null;
    try {
      eventSource = new EventSource(fullUrl);
      eventSource.addEventListener('connected', () => {
        if (onConnected) onConnected();
      });
      eventSource.addEventListener('notification', (event) => {
        try {
          const item = JSON.parse(event.data);
          onMessage(item);
        } catch (_) {}
      });
      eventSource.onmessage = (event) => {
        try {
          const item = JSON.parse(event.data);
          onMessage(item);
        } catch (_) {}
      };
    } catch (_) {}

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }
}

export const apiService = new ApiService(API_BASE_URL);
