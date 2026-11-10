export interface ThreatIndicator {
  indicator_type: string;
  indicator_value: string;
  threat_type: string;
  severity: string;
  confidence_score: number;
  source_name: string;
  source_reference?: string;
  description?: string;
  is_active: boolean;
  first_seen?: string;
  last_seen?: string;
}

export interface ThreatSearchResponse {
  query: string;
  indicator_type: string;
  is_threat_found: boolean;
  matched_indicator?: ThreatIndicator;
  source?: string;
  severity?: string;
  search_timestamp: string;
}

export interface ThreatIntelStatusResponse {
  module: string;
  engine_stage: string;
  service_status: string;
  total_active_indicators: number;
  by_type: Record<string, number>;
  sources: string[];
  last_feed_update?: string;
  feed_updater_status: string;
}

export interface UnifiedAnalyzeResponse {
  overall_risk_level: string;
  overall_risk_score: number;
  threat_category: string;
  is_corroborated: boolean;
  corroboration_notes: string[];
  intel_matches_count: number;
  intel_matches: any[];
  evidence_chain: Array<{
    layer: string;
    severity: string;
    title: string;
    details: string;
    source: string;
  }>;
  extracted_indicators: {
    urls: string[];
    domains: string[];
    ips: string[];
    upi_ids: string[];
    phones: string[];
  };
  modules: {
    url_detection?: any;
    communication_threat?: any;
    audio_detection?: any;
  };
  explanation: string;
  recommended_actions: string[];
  analysis_timestamp: string;
}

export interface LiveThreatEvent {
  id: number;
  event_type: string;
  severity: string;
  source_component: string;
  description: string;
  created_at: string;
}

