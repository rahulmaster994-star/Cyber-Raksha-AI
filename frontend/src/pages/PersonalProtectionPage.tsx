import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import type {
  ProtectionOverviewResponse,
  SecurityIncident,
  AssistantGuidanceResponse,
} from '../services/api';

export const PersonalProtectionPage: React.FC = () => {
  const [overview, setOverview] = useState<ProtectionOverviewResponse | null>(null);
  const [incidents, setIncidents] = useState<SecurityIncident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<SecurityIncident | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // New Incident Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCategory, setNewCategory] = useState('PHISHING');
  const [newTitle, setNewTitle] = useState('');
  const [newSeverity, setNewSeverity] = useState('HIGH');
  const [newSummary, setNewSummary] = useState('');

  // AI Security Guidance Assistant State
  const [assistantQuery, setAssistantQuery] = useState('');
  const [assistantResult, setAssistantResult] = useState<AssistantGuidanceResponse | null>(null);
  const [isAsking, setIsAsking] = useState(false);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    const [ovRes, incRes] = await Promise.all([
      apiService.getProtectionOverview(),
      apiService.getIncidents(statusFilter === 'ALL' ? undefined : statusFilter),
    ]);

    if (ovRes.data) setOverview(ovRes.data);
    if (incRes.data) {
      setIncidents(incRes.data.incidents);
      if (incRes.data.incidents.length > 0 && !selectedIncident) {
        setSelectedIncident(incRes.data.incidents[0]);
      }
    }
  };

  const handleCreateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newSummary.trim()) return;

    const res = await apiService.createIncident({
      category: newCategory,
      title: newTitle.trim(),
      severity: newSeverity,
      summary: newSummary.trim(),
    });

    if (res.data) {
      setShowCreateModal(false);
      setNewTitle('');
      setNewSummary('');
      loadData();
      setSelectedIncident(res.data);
    }
  };

  const handleCompleteAction = async (actionId: number) => {
    const res = await apiService.completeIncidentAction(actionId);
    if (res.data) {
      loadData();
      if (selectedIncident) {
        const updatedInc = await apiService.getIncidentById(selectedIncident.id);
        if (updatedInc.data) setSelectedIncident(updatedInc.data);
      }
    }
  };

  const handleResolveIncident = async (incId: number) => {
    const notes = prompt('Enter incident resolution notes:') || 'Mitigations completed by user.';
    const res = await apiService.updateIncidentStatus(incId, 'RESOLVED', notes);
    if (res.data) {
      loadData();
      setSelectedIncident(res.data);
    }
  };

  const handleAskAssistant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assistantQuery.trim()) return;
    setIsAsking(true);
    setAssistantResult(null);

    const res = await apiService.askAssistant(assistantQuery.trim());
    setIsAsking(false);
    if (res.data) {
      setAssistantResult(res.data);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev?.toUpperCase()) {
      case 'CRITICAL':
        return 'text-red-400 bg-red-950/40 border-red-500/40';
      case 'HIGH':
        return 'text-orange-400 bg-orange-950/40 border-orange-500/40';
      case 'MEDIUM':
        return 'text-amber-400 bg-amber-950/40 border-amber-500/40';
      default:
        return 'text-emerald-400 bg-emerald-950/40 border-emerald-500/40';
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st?.toUpperCase()) {
      case 'RESOLVED':
      case 'CLOSED':
        return 'text-emerald-400 bg-emerald-950/40 border-emerald-500/40';
      case 'CONTAINMENT_IN_PROGRESS':
        return 'text-cyan-400 bg-cyan-950/40 border-cyan-500/40';
      case 'ACTION_REQUIRED':
        return 'text-red-400 bg-red-950/40 border-red-500/40 animate-pulse';
      default:
        return 'text-amber-400 bg-amber-950/40 border-amber-500/40';
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="border border-cyan-500/30 bg-cyber-card/60 backdrop-blur-md rounded-2xl p-6 sm:p-8 relative overflow-hidden">
        <div className="absolute -right-12 -top-12 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium tracking-wide bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                STAGE 6 INCIDENT RESPONSE
              </span>
              <span className="text-xs font-mono text-gray-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                ACTIVE DEFENSE READY
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold font-mono tracking-tight text-white mt-2">
              Personal Protection & Incident Response Center
            </h1>
            <p className="text-gray-400 text-sm mt-1 max-w-2xl">
              Turn threat detection into decisive recovery action. Execute guided incident playbooks, track containment
              checklists, and consult the AI Security Guidance Assistant.
            </p>
          </div>

          <button
            onClick={() => setShowCreateModal(true)}
            className="px-5 py-2.5 rounded-lg font-mono text-xs font-semibold bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black shadow-lg shadow-cyan-500/20 transition-all shrink-0"
          >
            + Open Security Incident
          </button>
        </div>
      </div>

      {/* Security Posture Telemetry Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-cyber-card/40 border border-gray-800 backdrop-blur-sm">
          <div className="text-xs font-mono text-gray-400">DEFENSIVE POSTURE SCORE</div>
          <div className="text-2xl font-mono font-bold text-cyan-300 mt-1">
            {overview?.security_posture_score || 95.0}<span className="text-xs text-gray-500">/100</span>
          </div>
          <div className="text-[10px] text-emerald-400 font-mono mt-1">Active hygiene monitoring</div>
        </div>

        <div className="p-4 rounded-xl bg-cyber-card/40 border border-gray-800 backdrop-blur-sm">
          <div className="text-xs font-mono text-gray-400">ACTIVE INCIDENTS</div>
          <div className="text-2xl font-mono font-bold text-white mt-1">
            {overview?.active_incidents_count || 0}
          </div>
          <div className="text-[10px] text-amber-400 font-mono mt-1">Require containment actions</div>
        </div>

        <div className="p-4 rounded-xl bg-cyber-card/40 border border-gray-800 backdrop-blur-sm">
          <div className="text-xs font-mono text-gray-400">PENDING MITIGATIONS</div>
          <div className="text-2xl font-mono font-bold text-red-400 mt-1">
            {overview?.pending_actions_count || 0}
          </div>
          <div className="text-[10px] text-gray-400 font-mono mt-1">Checklist items remaining</div>
        </div>

        <div className="p-4 rounded-xl bg-cyber-card/40 border border-gray-800 backdrop-blur-sm">
          <div className="text-xs font-mono text-gray-400">CONTAINED & RESOLVED</div>
          <div className="text-2xl font-mono font-bold text-emerald-400 mt-1">
            {overview?.resolved_incidents_count || 0}
          </div>
          <div className="text-[10px] text-cyan-400 font-mono mt-1">Successfully recovered</div>
        </div>
      </div>

      {/* Guided AI Security Guidance Assistant */}
      <div className="border border-gray-800 bg-cyber-card/40 rounded-xl p-6 backdrop-blur-sm space-y-4">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          Guided AI Security Guidance Assistant
        </h2>
        <p className="text-xs text-gray-400">
          Ask urgent questions: e.g. "I shared my OTP with a caller", "What to do after clicking a suspicious link?", or "Fake police calling on Skype".
        </p>

        <form onSubmit={handleAskAssistant} className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={assistantQuery}
            onChange={(e) => setAssistantQuery(e.target.value)}
            placeholder="Type your security question or incident scenario here..."
            className="flex-1 px-4 py-2.5 rounded-lg bg-cyber-bg/70 border border-gray-700 text-white font-mono text-xs focus:outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            disabled={isAsking || !assistantQuery.trim()}
            className="px-6 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-mono font-semibold text-xs transition-all shrink-0"
          >
            {isAsking ? 'Consulting Playbooks...' : 'Get Security Guidance'}
          </button>
        </form>

        {assistantResult && (
          <div className="p-5 rounded-xl bg-cyber-bg/70 border border-cyan-500/40 space-y-3 mt-4">
            <div className="flex items-center justify-between pb-2 border-b border-gray-800">
              <span className="text-xs font-mono font-bold text-cyan-400">
                CATEGORY: {assistantResult.category}
              </span>
              <span className="text-[10px] font-mono text-gray-400">Evidence-Grounded Security Doctrine</span>
            </div>

            <p className="text-xs text-white leading-relaxed">{assistantResult.guidance_summary}</p>

            {assistantResult.action_steps.length > 0 && (
              <div className="space-y-1.5 pt-2">
                <span className="text-[10px] font-mono uppercase tracking-wider text-gray-400 block">Immediate Steps:</span>
                {assistantResult.action_steps.map((st, i) => (
                  <div key={i} className="text-xs text-gray-300 flex items-start gap-2">
                    <span className="text-cyan-400 font-bold">›</span>
                    {st}
                  </div>
                ))}
              </div>
            )}

            {assistantResult.official_resources.length > 0 && (
              <div className="pt-2 border-t border-gray-800 flex flex-wrap gap-4 text-xs font-mono text-gray-300">
                <span className="text-gray-500 text-[10px] uppercase">Official Reporting:</span>
                {assistantResult.official_resources.map((res, i) => (
                  <div key={i} className="text-cyan-400">
                    {res.name}: <strong className="text-white">{res.contact || res.url}</strong>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Main Incident Workbench */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Incident List Column */}
        <div className="lg:col-span-1 border border-gray-800 bg-cyber-card/40 rounded-xl p-5 backdrop-blur-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-mono uppercase tracking-wider text-white font-semibold">
              Security Incidents ({incidents.length})
            </h3>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2 py-1 bg-cyber-bg/70 border border-gray-700 rounded text-[10px] font-mono text-gray-300 focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTION_REQUIRED">Action Required</option>
              <option value="CONTAINMENT_IN_PROGRESS">In Progress</option>
              <option value="RESOLVED">Resolved</option>
            </select>
          </div>

          {incidents.length > 0 ? (
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
              {incidents.map((inc) => (
                <div
                  key={inc.id}
                  onClick={() => setSelectedIncident(inc)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedIncident?.id === inc.id
                      ? 'border-cyan-500 bg-cyan-950/20'
                      : 'border-gray-800 bg-cyber-bg/40 hover:border-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between font-mono text-xs">
                    <span className="text-white font-bold">{inc.incident_number}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${getStatusBadge(inc.status)}`}>
                      {inc.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-300 mt-1 font-medium truncate">{inc.title}</p>
                  <div className="text-[10px] text-gray-500 font-mono flex items-center justify-between mt-2">
                    <span className={`px-1 py-0.2 rounded border ${getSeverityBadge(inc.severity)}`}>{inc.severity}</span>
                    <span>{new Date(inc.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-500 text-center py-8 font-mono">
              No active incidents logged. Click "+ Open Security Incident" to register one.
            </p>
          )}
        </div>

        {/* Selected Incident Detail & Guided Actions */}
        <div className="lg:col-span-2 border border-gray-800 bg-cyber-card/60 rounded-xl p-6 backdrop-blur-md space-y-6">
          {selectedIncident ? (
            <>
              {/* Incident Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-800">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-cyan-400 font-bold">{selectedIncident.incident_number}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${getSeverityBadge(selectedIncident.severity)}`}>
                      {selectedIncident.severity} SEVERITY
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${getStatusBadge(selectedIncident.status)}`}>
                      {selectedIncident.status}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white mt-1">{selectedIncident.title}</h3>
                  <p className="text-xs text-gray-400 mt-0.5 font-mono">Category: {selectedIncident.category}</p>
                </div>

                {selectedIncident.status !== 'RESOLVED' && selectedIncident.status !== 'CLOSED' && (
                  <button
                    onClick={() => handleResolveIncident(selectedIncident.id)}
                    className="px-4 py-1.5 rounded-lg border border-emerald-500/40 text-emerald-400 hover:bg-emerald-950/30 font-mono text-xs font-semibold transition-all shrink-0"
                  >
                    Mark Incident Resolved ✓
                  </button>
                )}
              </div>

              {/* Summary */}
              <div className="p-4 rounded-lg bg-cyber-bg/40 border border-gray-800 text-xs text-gray-300 leading-relaxed font-mono">
                <span className="text-gray-500 uppercase block mb-1">Incident Summary & Evidence:</span>
                {selectedIncident.summary}
                {selectedIncident.evidence_references && (
                  <div className="mt-2 text-cyan-300">Target / Evidence: {selectedIncident.evidence_references}</div>
                )}
              </div>

              {/* Actions Checklist */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-mono uppercase tracking-wider text-white font-semibold">
                    Guided Containment & Recovery Actions ({selectedIncident.actions.length})
                  </h4>
                  <span className="text-[10px] font-mono text-cyan-400">
                    {selectedIncident.actions.filter((a) => a.is_completed).length} / {selectedIncident.actions.length} Completed
                  </span>
                </div>

                <div className="space-y-2.5">
                  {selectedIncident.actions.map((act) => (
                    <div
                      key={act.id}
                      className={`p-3.5 rounded-lg border flex items-start justify-between gap-4 transition-all ${
                        act.is_completed
                          ? 'border-emerald-500/30 bg-emerald-950/10 opacity-75'
                          : 'border-gray-800 bg-cyber-bg/40 hover:border-gray-700'
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${act.is_completed ? 'bg-emerald-400' : 'bg-red-400'}`} />
                          <span className={`text-xs font-mono font-bold ${act.is_completed ? 'line-through text-gray-400' : 'text-white'}`}>
                            {act.title}
                          </span>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-gray-800 text-gray-400">
                            {act.priority}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 leading-normal">{act.description}</p>
                      </div>

                      <button
                        onClick={() => handleCompleteAction(act.id)}
                        disabled={act.is_completed}
                        className={`px-3 py-1.5 rounded font-mono text-xs font-semibold shrink-0 transition-all ${
                          act.is_completed
                            ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/40 cursor-default'
                            : 'bg-cyan-500 hover:bg-cyan-400 text-black shadow-md shadow-cyan-500/20'
                        }`}
                      >
                        {act.is_completed ? 'Done ✓' : 'Mark Completed'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-16 text-gray-500 font-mono text-xs">
              Select an incident from the left panel to review its guided containment checklist.
            </div>
          )}
        </div>
      </div>

      {/* Create Incident Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="border border-cyan-500/40 bg-cyber-card p-6 rounded-2xl max-w-lg w-full space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-gray-800">
              <h3 className="text-base font-bold text-white font-mono">Open New Security Incident</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleCreateIncident} className="space-y-4 text-xs font-mono">
              <div>
                <label className="text-gray-300 block mb-1">INCIDENT CATEGORY</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full p-2.5 bg-cyber-bg border border-gray-700 rounded text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="PHISHING">Phishing Attack</option>
                  <option value="FINANCIAL_FRAUD">Financial Fraud / UPI Scam</option>
                  <option value="DIGITAL_ARREST">Digital Arrest Extortion</option>
                  <option value="VOICE_CLONING">Voice Cloning / Audio Impersonation</option>
                  <option value="ACCOUNT_COMPROMISE">Account Compromise (OTP/Password Shared)</option>
                </select>
              </div>

              <div>
                <label className="text-gray-300 block mb-1">INCIDENT TITLE</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Clicked SMS link asking for Aadhaar verification"
                  className="w-full p-2.5 bg-cyber-bg border border-gray-700 rounded text-white focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div>
                <label className="text-gray-300 block mb-1">SEVERITY LEVEL</label>
                <select
                  value={newSeverity}
                  onChange={(e) => setNewSeverity(e.target.value)}
                  className="w-full p-2.5 bg-cyber-bg border border-gray-700 rounded text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="CRITICAL">Critical (Active Fund Loss / Blackmail)</option>
                  <option value="HIGH">High (Credentials Disclosed)</option>
                  <option value="MEDIUM">Medium (Suspicious Engagement)</option>
                  <option value="LOW">Low (Benign Ingestion)</option>
                </select>
              </div>

              <div>
                <label className="text-gray-300 block mb-1">DETAILS & EVIDENCE</label>
                <textarea
                  value={newSummary}
                  onChange={(e) => setNewSummary(e.target.value)}
                  rows={4}
                  placeholder="Describe what occurred, any phone numbers/URLs involved..."
                  className="w-full p-2.5 bg-cyber-bg border border-gray-700 rounded text-white focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded bg-gray-800 hover:bg-gray-700 text-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded bg-cyan-500 hover:bg-cyan-400 text-black font-bold shadow-md shadow-cyan-500/20"
                >
                  Create & Launch Playbook
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
