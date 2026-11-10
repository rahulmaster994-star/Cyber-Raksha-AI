export interface IncidentAction {
  id: number;
  action_key: string;
  title: string;
  description: string;
  priority: string;
  is_completed: boolean;
  completed_at?: string;
  created_at: string;
}

export interface SecurityIncident {
  id: number;
  incident_number: string;
  category: string;
  title: string;
  severity: string;
  status: string;
  summary: string;
  related_analysis_id?: number;
  evidence_references?: string;
  resolution_notes?: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
  actions: IncidentAction[];
}

export interface IncidentListResponse {
  total_count: number;
  incidents: SecurityIncident[];
}

export interface ProtectionOverviewResponse {
  active_incidents_count: number;
  resolved_incidents_count: number;
  pending_actions_count: number;
  completed_actions_count: number;
  security_posture_score: number;
  recent_incidents: SecurityIncident[];
  available_playbooks_count: number;
  privacy_mode: string;
}

export interface AssistantGuidanceResponse {
  query: string;
  category: string;
  guidance_summary: string;
  action_steps: string[];
  official_resources: Array<{ name: string; contact?: string; url?: string }>;
  disclaimer: string;
}

export interface ResponsePlaybook {
  id: string;
  category: string;
  title: string;
  description: string;
  steps: Array<{
    step_number: number;
    action_key: string;
    title: string;
    priority: string;
    description: string;
    is_user_confirmation_required: boolean;
  }>;
}
