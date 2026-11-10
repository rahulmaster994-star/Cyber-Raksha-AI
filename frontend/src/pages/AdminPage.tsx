import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldAlert,
  Server,
  Activity,
  Cpu,
  Layers,
  Database,
  Lock,
  Unlock,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Sliders,
  Check,
  X
} from 'lucide-react';
import { apiService } from '../services/api';

export const AdminPage: React.FC = () => {
  const [adminKey, setAdminKey] = useState<string>(() => {
    return sessionStorage.getItem('cyber_raksha_admin_key') || '';
  });
  const [inputKey, setInputKey] = useState<string>('');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Data states
  const [overview, setOverview] = useState<any>(null);
  const [flags, setFlags] = useState<Record<string, any>>({});
  const [pendingFeedback, setPendingFeedback] = useState<any[]>([]);
  const [feedHealth, setFeedHealth] = useState<any>(null);
  const [models, setModels] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'flags' | 'feedback' | 'feeds' | 'models'>('overview');

  // Review action modal/inputs
  const [reviewNotes, setReviewNotes] = useState<Record<number, string>>({});

  const fetchAdminData = useCallback(async (key: string) => {
    if (!key) return;
    setLoading(true);
    setAuthError(null);

    try {
      const res = await apiService.getAdminOverview(key);
      if (res.error) {
        setIsAuthenticated(false);
        setAuthError(res.error);
        setLoading(false);
        return;
      }

      setIsAuthenticated(true);
      setOverview(res.data);
      sessionStorage.setItem('cyber_raksha_admin_key', key);

      // Concurrently fetch additional admin feeds
      const [flagsRes, feedbackRes, feedsRes, modelsRes, alertsRes] = await Promise.all([
        apiService.getFeatureFlags(key),
        apiService.getPendingFeedback(key),
        apiService.getFeedHealth(),
        apiService.getModelsOverview(),
        apiService.getAdminAlerts(key),
      ]);

      if (flagsRes.data?.feature_flags) setFlags(flagsRes.data.feature_flags);
      if (feedbackRes.data?.feedback) setPendingFeedback(feedbackRes.data.feedback);
      if (feedsRes.data) setFeedHealth(feedsRes.data);
      if (modelsRes.data?.models) setModels(modelsRes.data.models);
      if (alertsRes.data?.alerts) setAlerts(alertsRes.data.alerts);

    } catch (e: any) {
      setAuthError(e.message || 'Connection error');
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (adminKey) {
      fetchAdminData(adminKey);
    }
  }, [adminKey, fetchAdminData]);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputKey.trim()) return;
    setAdminKey(inputKey.trim());
    fetchAdminData(inputKey.trim());
  };

  const handleLogout = () => {
    sessionStorage.removeItem('cyber_raksha_admin_key');
    setAdminKey('');
    setIsAuthenticated(false);
    setOverview(null);
  };

  const toggleFlag = async (flagName: string, currentEnabled: boolean) => {
    const newEnabled = !currentEnabled;
    const res = await apiService.updateFeatureFlag(adminKey, flagName, newEnabled);
    if (!res.error) {
      setFlags((prev) => ({
        ...prev,
        [flagName]: { ...prev[flagName], enabled: newEnabled }
      }));
    }
  };

  const handleReviewVerdict = async (feedbackId: number, status: string) => {
    const notes = reviewNotes[feedbackId] || '';
    const res = await apiService.reviewFeedback(adminKey, feedbackId, status, notes);
    if (!res.error) {
      setPendingFeedback((prev) => prev.filter((item) => item.feedback_id !== feedbackId));
    }
  };

  const handleClearAlerts = async () => {
    await apiService.clearAlerts(adminKey);
    setAlerts([]);
    if (overview) {
      setOverview({
        ...overview,
        alerts: { ...overview.alerts, active_alerts: 0 }
      });
    }
  };

  // Auth gate
  if (!isAuthenticated) {
    return (
      <div className="max-w-md mx-auto my-20 p-6 rounded-2xl bg-[#0A0F1D] border border-[#1E2E5C] shadow-2xl">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Lock className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Operations Center</h2>
            <p className="text-xs text-gray-400">Stage 9 Administrative Control Interface</p>
          </div>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-gray-300 mb-2">
              ADMIN SECRET KEY (X-Admin-Key)
            </label>
            <input
              type="password"
              value={inputKey}
              onChange={(e) => setInputKey(e.target.value)}
              placeholder="Enter ADMIN_SECRET_KEY..."
              className="w-full bg-[#050811] border border-[#1E2E5C] rounded-lg px-4 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>

          {authError && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{authError}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !inputKey.trim()}
            className="w-full py-2.5 rounded-lg bg-cyan-500 text-black font-semibold text-sm hover:bg-cyan-400 disabled:opacity-50 transition-all flex items-center justify-center space-x-2"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Unlock className="w-4 h-4" />
            )}
            <span>Authenticate to Operations Center</span>
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-[#0A0F1D] border border-[#1E2E5C]">
        <div className="flex items-center space-x-3">
          <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 text-cyan-400 shadow-[0_0_15px_rgba(0,240,255,0.2)]">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-white tracking-wide">
                CYBER RAKSHA OPERATIONS CENTER
              </h1>
              <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-mono">
                Stage 9
              </span>
            </div>
            <p className="text-xs text-gray-400">
              Real-time Pilot Monitoring, Observability, Feature Flags & Governance
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => fetchAdminData(adminKey)}
            disabled={loading}
            className="p-2 rounded-lg border border-[#1E2E5C] text-gray-300 hover:text-cyan-400 transition-colors"
            title="Refresh All"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-300 text-xs font-mono hover:bg-rose-500/20 transition-all"
          >
            Disconnect Admin
          </button>
        </div>
      </div>

      {/* Active Alerts Banner */}
      {overview?.alerts?.active_alerts > 0 && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <ShieldAlert className="w-5 h-5 text-amber-400" />
              <div>
                <h4 className="text-sm font-semibold text-amber-300">
                  {overview.alerts.active_alerts} Active Operational Alert(s)
                </h4>
                <p className="text-xs text-amber-200/80">
                  Subsystems require operator inspection.
                </p>
              </div>
            </div>
            <button
              onClick={handleClearAlerts}
              className="px-3 py-1 text-xs rounded bg-amber-500 text-black font-semibold hover:bg-amber-400 transition-colors"
            >
              Acknowledge All
            </button>
          </div>
          {alerts.length > 0 && (
            <div className="pt-2 border-t border-amber-500/20 space-y-1 text-xs font-mono">
              {alerts.filter((a) => !a.acknowledged).slice(0, 3).map((a) => (
                <div key={a.alert_id} className="text-amber-200">
                  [{a.severity}] {a.alert_type} ({a.source}): {a.message}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Telemetry Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#0A0F1D] border border-[#1E2E5C]">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-2">
            <span>PLATFORM HEALTH</span>
            <Server className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-emerald-400 font-mono">
            {overview?.overall_health || 'HEALTHY'}
          </div>
          <div className="text-[11px] text-gray-500 mt-1">
            Uptime: {overview?.performance?.uptime_seconds ? `${Math.round(overview.performance.uptime_seconds)}s` : 'Active'}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#0A0F1D] border border-[#1E2E5C]">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-2">
            <span>P95 LATENCY</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-lg font-bold text-white font-mono">
            {overview?.performance?.p95_latency_ms ?? 0} ms
          </div>
          <div className="text-[11px] text-gray-500 mt-1">
            Total Requests: {overview?.performance?.total_requests ?? 0}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#0A0F1D] border border-[#1E2E5C]">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-2">
            <span>FEED FRESHNESS</span>
            <Database className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-lg font-bold text-amber-400 font-mono">
            {overview?.threat_intel?.healthy_sources || 0} / 3 Feeds
          </div>
          <div className="text-[11px] text-gray-500 mt-1">
            {overview?.threat_intel?.total_active_indicators || 0} active IoCs
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#0A0F1D] border border-[#1E2E5C]">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-2">
            <span>PENDING REVIEWS</span>
            <Layers className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-lg font-bold text-purple-400 font-mono">
            {pendingFeedback.length} Items
          </div>
          <div className="text-[11px] text-gray-500 mt-1">
            Human Governance Queue
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#1E2E5C] space-x-2 text-sm">
        {(['overview', 'flags', 'feedback', 'feeds', 'models'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium capitalize border-b-2 transition-all ${
              activeTab === tab
                ? 'border-cyan-400 text-cyan-400 bg-cyan-500/10'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            {tab === 'flags' ? 'Feature Flags' : tab === 'feedback' ? `Human Review (${pendingFeedback.length})` : tab}
          </button>
        ))}
      </div>

      {/* Tab 1: Overview & Subsystems */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Subsystem Health Breakdown */}
            <div className="p-5 rounded-xl bg-[#0A0F1D] border border-[#1E2E5C] space-y-4">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center space-x-2">
                <Server className="w-4 h-4 text-cyan-400" />
                <span>Subsystem Status Breakdown</span>
              </h3>
              <div className="space-y-3">
                {overview?.subsystems && Object.entries(overview.subsystems).map(([key, val]: any) => (
                  <div key={key} className="flex items-center justify-between p-3 rounded-lg bg-slate-900/60 border border-[#1E2E5C]/50">
                    <span className="text-xs font-mono text-gray-300 uppercase">{key.replace('_', ' ')}</span>
                    <span className={`text-xs px-2 py-0.5 rounded font-mono font-semibold ${
                      val === 'HEALTHY' || val?.status === 'HEALTHY' || val?.status === 'ACTIVE'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    }`}>
                      {typeof val === 'string' ? val : val?.status || 'ONLINE'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Analysis Jobs */}
            <div className="p-5 rounded-xl bg-[#0A0F1D] border border-[#1E2E5C] space-y-4">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center space-x-2">
                <Activity className="w-4 h-4 text-purple-400" />
                <span>Recent Analysis Jobs</span>
              </h3>
              <div className="space-y-2">
                {overview?.jobs?.recent?.length > 0 ? (
                  overview.jobs.recent.map((j: any) => (
                    <div key={j.job_id} className="flex items-center justify-between p-3 rounded-lg bg-slate-900/60 border border-[#1E2E5C]/50 text-xs font-mono">
                      <div>
                        <span className="text-cyan-400">{j.job_id}</span>
                        <span className="text-gray-500 ml-2">({j.job_type})</span>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-gray-300 border border-slate-700">
                        {j.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-500 py-4 text-center">No recent background jobs.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Feature Flags Management */}
      {activeTab === 'flags' && (
        <div className="p-6 rounded-xl bg-[#0A0F1D] border border-[#1E2E5C] space-y-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-base font-semibold text-white">Dynamic Feature Flags</h3>
              <p className="text-xs text-gray-400">
                Disable malfunctioning subsystems instantly without redeploying the application.
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {Object.entries(flags).map(([key, flag]: any) => (
              <div
                key={key}
                className="flex items-center justify-between p-4 rounded-xl bg-slate-900/60 border border-[#1E2E5C]/60 hover:border-cyan-500/40 transition-all"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-mono font-medium text-white">{key}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-gray-400 font-mono">
                      {flag.category}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">{flag.description}</p>
                </div>

                <button
                  onClick={() => toggleFlag(key, flag.enabled)}
                  className={`px-4 py-2 rounded-lg font-mono text-xs font-semibold flex items-center space-x-1.5 transition-all ${
                    flag.enabled
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                  }`}
                >
                  {flag.enabled ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>ENABLED</span>
                    </>
                  ) : (
                    <>
                      <X className="w-3.5 h-3.5" />
                      <span>DISABLED</span>
                    </>
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Human Review Feedback Queue */}
      {activeTab === 'feedback' && (
        <div className="p-6 rounded-xl bg-[#0A0F1D] border border-[#1E2E5C] space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-white">Human Review Queue</h3>
              <p className="text-xs text-gray-400">
                Triage user feedback submissions. Confirmed items enter candidate retraining pools for offline evaluation.
              </p>
            </div>
            <span className="text-xs font-mono text-cyan-400 px-2 py-1 rounded bg-cyan-500/10 border border-cyan-500/30">
              {pendingFeedback.length} Pending
            </span>
          </div>

          {pendingFeedback.length === 0 ? (
            <div className="py-12 text-center text-gray-500 text-sm">
              <CheckCircle className="w-8 h-8 text-emerald-500/40 mx-auto mb-2" />
              Human review queue is empty. All feedback has been processed.
            </div>
          ) : (
            <div className="space-y-4">
              {pendingFeedback.map((item) => (
                <div key={item.feedback_id} className="p-4 rounded-xl bg-slate-900/70 border border-[#1E2E5C] space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-cyan-400">ID #{item.feedback_id}</span>
                    <span className="px-2 py-0.5 rounded font-mono font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      {item.feedback_category}
                    </span>
                  </div>

                  {item.target_identifier && (
                    <div className="text-xs font-mono text-gray-300 bg-black/40 p-2 rounded truncate border border-slate-800">
                      Target: {item.target_identifier}
                    </div>
                  )}

                  {item.user_explanation && (
                    <p className="text-xs text-gray-300 italic">
                      "{item.user_explanation}"
                    </p>
                  )}

                  <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-800">
                    <input
                      type="text"
                      placeholder="Analyst verdict notes..."
                      value={reviewNotes[item.feedback_id] || ''}
                      onChange={(e) => setReviewNotes({ ...reviewNotes, [item.feedback_id]: e.target.value })}
                      className="w-full sm:w-80 bg-[#050811] border border-[#1E2E5C] rounded px-3 py-1.5 text-xs text-gray-200"
                    />

                    <div className="flex items-center space-x-2 shrink-0">
                      <button
                        onClick={() => handleReviewVerdict(item.feedback_id, 'CONFIRMED')}
                        className="px-3 py-1.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold hover:bg-emerald-500/30 flex items-center space-x-1"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Confirm</span>
                      </button>
                      <button
                        onClick={() => handleReviewVerdict(item.feedback_id, 'REJECTED')}
                        className="px-3 py-1.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-semibold hover:bg-rose-500/30 flex items-center space-x-1"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                      <button
                        onClick={() => handleReviewVerdict(item.feedback_id, 'INCONCLUSIVE')}
                        className="px-3 py-1.5 rounded bg-slate-800 text-gray-400 text-xs hover:text-white"
                      >
                        Inconclusive
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Feeds Health & Limitations */}
      {activeTab === 'feeds' && (
        <div className="p-6 rounded-xl bg-[#0A0F1D] border border-[#1E2E5C] space-y-4">
          <h3 className="text-base font-semibold text-white">Threat Intelligence Sources & Freshness</h3>
          <div className="space-y-4">
            {feedHealth?.sources?.map((s: any) => (
              <div key={s.key} className="p-4 rounded-xl bg-slate-900/60 border border-[#1E2E5C] space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-semibold text-white">{s.name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-gray-400 font-mono">
                      {s.type}
                    </span>
                  </div>
                  <span className={`text-xs px-2.5 py-1 rounded font-mono font-semibold ${
                    s.freshness.includes('FRESH')
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  }`}>
                    {s.freshness}
                  </span>
                </div>

                <div className="text-xs text-gray-400 grid grid-cols-2 md:grid-cols-4 gap-2 pt-2">
                  <div>Status: <span className="text-gray-200 font-mono">{s.status}</span></div>
                  <div>Imported: <span className="text-cyan-400 font-mono">{s.indicators_imported}</span></div>
                  <div>Rate Limit: <span className="text-gray-200 font-mono">{s.rate_limit_rpm} rpm</span></div>
                  <div>Last Update: <span className="text-gray-200 font-mono">{s.last_successful_update ? s.last_successful_update.substring(0, 10) : 'Offline Cached'}</span></div>
                </div>

                {s.limitations && s.limitations.length > 0 && (
                  <div className="mt-2 p-2 rounded bg-black/40 border border-slate-800 text-[11px] text-gray-400">
                    <span className="text-amber-300 font-medium">Known Limitations: </span>
                    {s.limitations.join(' ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 5: AI Model Performance & Drift */}
      {activeTab === 'models' && (
        <div className="p-6 rounded-xl bg-[#0A0F1D] border border-[#1E2E5C] space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-white">Deployed AI Models Benchmark Registry</h3>
              <p className="text-xs text-gray-400">
                Verified evaluation metrics from controlled held-out splits.
              </p>
            </div>
            <div className="text-xs font-mono text-amber-300 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded">
              Zero Automatic Retraining Policy Active
            </div>
          </div>

          <div className="space-y-4">
            {models.map((m) => (
              <div key={m.model_id} className="p-4 rounded-xl bg-slate-900/60 border border-[#1E2E5C] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Cpu className="w-4 h-4 text-cyan-400" />
                    <span className="text-sm font-bold text-white font-mono">{m.model_id}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono">
                      {m.model_version}
                    </span>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                    {m.deployment_status}
                  </span>
                </div>

                <div className="text-xs text-gray-400">
                  Algorithm: <span className="text-gray-200">{m.model_type}</span>
                </div>

                {/* Benchmark Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-xs font-mono">
                  <div className="p-2 rounded bg-black/40 border border-slate-800">
                    <div className="text-gray-500">ACCURACY</div>
                    <div className="text-emerald-400 font-bold">{(m.metrics?.accuracy * 100).toFixed(1)}%</div>
                  </div>
                  <div className="p-2 rounded bg-black/40 border border-slate-800">
                    <div className="text-gray-500">PRECISION</div>
                    <div className="text-cyan-400 font-bold">{(m.metrics?.precision * 100).toFixed(1)}%</div>
                  </div>
                  <div className="p-2 rounded bg-black/40 border border-slate-800">
                    <div className="text-gray-500">RECALL</div>
                    <div className="text-blue-400 font-bold">{(m.metrics?.recall * 100).toFixed(1)}%</div>
                  </div>
                  <div className="p-2 rounded bg-black/40 border border-slate-800">
                    <div className="text-gray-500">F1 SCORE</div>
                    <div className="text-purple-400 font-bold">{(m.metrics?.f1_score * 100).toFixed(1)}%</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPage;
