export interface AudioMetadata {
  filename?: string;
  file_size_bytes?: number;
  duration_seconds?: number;
  sample_rate?: number;
  channels?: number;
  bit_depth?: number;
  format?: string;
}

export interface AudioIndicator {
  code: string;
  name: string;
  severity: string;
  description: string;
  score_weight: number;
}

export interface AudioAnalysisResponse {
  status: string;
  classification: string;
  risk_level: string;
  risk_score: number;
  confidence: number;
  ml_probability: number;
  indicator_score: number;
  indicators_count: number;
  detected_indicators: AudioIndicator[];
  spectral_metrics: Record<string, any>;
  audio_metadata: AudioMetadata;
  explanation: string;
  recommendations: string[];
  is_inconclusive: boolean;
  inconclusive_reason?: string;
  engine_version: string;
  model_version?: string;
  forensic_capability_scope?: string;
  biometric_identity_supported?: boolean;
}

export interface AudioStatusResponse {
  module: string;
  model_available: boolean;
  model_loaded: boolean;
  model_name: string;
  model_type: string;
  stage: string;
  accuracy?: number;
  features_count: number;
  supported_formats: string[];
  disclaimer: string;
  forensic_capability_scope?: string;
  biometric_identity_supported?: boolean;
}

