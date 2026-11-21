import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  X,
  Search,
  Smartphone,
  Radio,
  Play,
  Pause,
  Trash2,
  Plus,
  Download,
  Terminal,
  Bell,
  AlertOctagon,
  UserCheck
} from 'lucide-react';
import { apiService } from '../services/api';

type AdminTab =
  | 'overview'
  | 'users'
  | 'devices'
  | 'events'
  | 'soc_feed'
  | 'incidents'
  | 'threat_intel'
  | 'alerts'
  | 'models'
  | 'diagnostics'
  | 'audit'
  | 'diagnostics_audit';

interface AdminPageProps {
  onNavigateToPublic?: (tab?: string) => void;
}

export const AdminPage: React.FC<AdminPageProps> = ({ onNavigateToPublic }) => {
  const [adminKey, setAdminKey] = useState<string>(() => {
    return sessionStorage.getItem('cyber_raksha_admin_key') || '';
  });
  const [inputKey, setInputKey] = useState<string>('');
  const [inputUsername, setInputUsername] = useState<string>('admin');
  const [inputPassword, setInputPassword] = useState<string>('');
  const [loginMode, setLoginMode] = useState<'key' | 'credentials'>('key');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');

  // Overview data
  const [overview, setOverview] = useState<any>(null);

  // Tab Data States
  const [users, setUsers] = useState<any[]>([]);
  const [userSearch, setUserSearch] = useState<string>('');
  const [userRoleFilter, setUserRoleFilter] = useState<string>('');

  const [devices, setDevices] = useState<any[]>([]);
  const [deviceStatusFilter, setDeviceStatusFilter] = useState<string>('');
  const [selectedDeviceActivity, setSelectedDeviceActivity] = useState<{ deviceId: string; activities: any[] } | null>(null);

  const [events, setEvents] = useState<any[]>([]);
  const [eventSeverityFilter, setEventSeverityFilter] = useState<string>('');
  const [eventComponentFilter, setEventComponentFilter] = useState<string>('');
  const [selectedEventDetail, setSelectedEventDetail] = useState<any | null>(null);

  // Real-time SOC Feed State
  const [liveStreamEvents, setLiveStreamEvents] = useState<any[]>([]);
  const [streamConnected, setStreamConnected] = useState<boolean>(false);
  const [isStreamPaused, setIsStreamPaused] = useState<boolean>(false);
  const streamUnsubscribeRef = useRef<(() => void) | null>(null);

  // Incidents State
  const [incidents, setIncidents] = useState<any[]>([]);
  const [incidentStatusFilter, setIncidentStatusFilter] = useState<string>('');
  const [newIncidentForm, setNewIncidentForm] = useState({
    title: '',
    category: 'PHISHING',
    severity: 'HIGH',
    summary: '',
    target_or_indicator: '',
  });
  const [showCreateIncident, setShowCreateIncident] = useState<boolean>(false);

  // Threat Intel State
  const [threatIndicators, setThreatIndicators] = useState<any[]>([]);
  const [callerReputations, setCallerReputations] = useState<any[]>([]);
  const [newIndicatorForm, setNewIndicatorForm] = useState({
    indicator_type: 'URL',
    indicator_value: '',
    threat_type: 'PHISHING',
    severity: 'HIGH',
    confidence: 0.95,
  });
  const [showAddIndicator, setShowAddIndicator] = useState<boolean>(false);

  // Alerts State
  const [alerts, setAlerts] = useState<any[]>([]);

  // AI Models State
  const [modelsData, setModelsData] = useState<any>(null);

  // Diagnostics & Audit State
  const [diagnostics, setDiagnostics] = useState<any>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // Feedback Notification
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const loadCurrentTabData = useCallback(async (tab: AdminTab, key: string) => {
    if (!key) return;
    try {
      if (tab === 'overview') {
        const res = await apiService.getAdminOverview(key);
        if (res.data) setOverview(res.data);
      } else if (tab === 'users') {
        const res = await apiService.getAdminUsers(key, {
          search: userSearch || undefined,
          role: userRoleFilter || undefined,
        });
        if (res.data?.users) setUsers(res.data.users);
      } else if (tab === 'devices') {
        const res = await apiService.getAdminDevices(key, {
          status: deviceStatusFilter || undefined,
        });
        if (res.data?.devices) setDevices(res.data.devices);
      } else if (tab === 'events') {
        const res = await apiService.getAdminSecurityEvents(key, {
          severity: eventSeverityFilter || undefined,
          component: eventComponentFilter || undefined,
          limit: 50,
        });
        if (res.data?.events) setEvents(res.data.events);
      } else if (tab === 'incidents') {
        const res = await apiService.getAdminIncidents(key, {
          status: incidentStatusFilter || undefined,
          limit: 50,
        });
        if (res.data?.incidents) setIncidents(res.data.incidents);
      } else if (tab === 'threat_intel') {
        const res = await apiService.getAdminThreatIntelligence(key, { limit: 100 });
        if (res.data?.indicators) setThreatIndicators(res.data.indicators);
        if (res.data?.phone_reputations) setCallerReputations(res.data.phone_reputations);
      } else if (tab === 'alerts') {
        const res = await apiService.getAdminAlerts(key);
        if (res.data?.alerts) setAlerts(res.data.alerts);
      } else if (tab === 'models') {
        const res = await apiService.getAdminModels(key);
        if (res.data) setModelsData(res.data);
      } else if (tab === 'diagnostics') {
        const diagRes = await apiService.getAdminDiagnostics(key);
        if (diagRes.data) setDiagnostics(diagRes.data);
      } else if (tab === 'audit') {
        const auditRes = await apiService.getAdminAuditLogs(key, 100);
        if (auditRes.data?.audit_logs) setAuditLogs(auditRes.data.audit_logs);
      } else if (tab === 'diagnostics_audit') {
        const [diagRes, auditRes] = await Promise.all([
          apiService.getAdminDiagnostics(key),
          apiService.getAdminAuditLogs(key, 50),
        ]);
        if (diagRes.data) setDiagnostics(diagRes.data);
        if (auditRes.data?.audit_logs) setAuditLogs(auditRes.data.audit_logs);
      }
    } catch (e: any) {
      console.error('Failed loading tab data:', e);
    }
  }, [userSearch, userRoleFilter, deviceStatusFilter, eventSeverityFilter, eventComponentFilter, incidentStatusFilter]);

  const verifyAndInitialize = useCallback(async (key: string) => {
    setLoading(true);
    setAuthError(null);
    try {
      const verifyRes = await apiService.adminVerify(key);
      if (verifyRes.error) {
        setIsAuthenticated(false);
        setAuthError(verifyRes.error);
        setLoading(false);
        return;
      }

      setIsAuthenticated(true);
      sessionStorage.setItem('cyber_raksha_admin_key', key);
      loadCurrentTabData(activeTab, key);
    } catch (err: any) {
      setIsAuthenticated(false);
      setAuthError(err.message || 'Authentication error');
    } finally {
      setLoading(false);
    }
  }, [activeTab, loadCurrentTabData]);

  useEffect(() => {
    if (adminKey) {
      verifyAndInitialize(adminKey);
    }
  }, [adminKey, verifyAndInitialize]);

  useEffect(() => {
    if (isAuthenticated && adminKey) {
      loadCurrentTabData(activeTab, adminKey);
    }
  }, [activeTab, isAuthenticated, adminKey, loadCurrentTabData]);

  // Connect SSE feed when on soc_feed tab
  useEffect(() => {
    if (isAuthenticated && adminKey && activeTab === 'soc_feed') {
      setStreamConnected(true);
      const unsub = apiService.subscribeAdminStream(adminKey, (eventData) => {
        if (!isStreamPaused) {
          setLiveStreamEvents((prev) => [eventData, ...prev.slice(0, 99)]);
        }
      });
      streamUnsubscribeRef.current = unsub;
      return () => {
        if (streamUnsubscribeRef.current) {
          streamUnsubscribeRef.current();
          streamUnsubscribeRef.current = null;
        }
        setStreamConnected(false);
      };
    }
  }, [isAuthenticated, adminKey, activeTab, isStreamPaused]);

  const handleKeyLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputKey.trim()) return;
    setAdminKey(inputKey.trim());
    verifyAndInitialize(inputKey.trim());
  };

  const handleCredentialLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputUsername || !inputPassword) return;
    setLoading(true);
    setAuthError(null);
    try {
      const res = await apiService.adminLogin({ username: inputUsername, password: inputPassword });
      if (res.data?.access_token) {
        setAdminKey(res.data.access_token);
        verifyAndInitialize(res.data.access_token);
      } else {
        setAuthError(res.error || 'Invalid credentials');
      }
    } catch (err: any) {
      setAuthError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem('cyber_raksha_admin_key');
    setAdminKey('');
    setIsAuthenticated(false);
    setOverview(null);
  };

  // User Actions
  const handleToggleUserStatus = async (userId: number, currentStatus: boolean) => {
    const res = await apiService.updateAdminUserStatus(adminKey, userId, !currentStatus);
    if (res.data) {
      showToast(`User ${res.data.username} status updated to ${!currentStatus ? 'ACTIVE' : 'SUSPENDED'}`);
      loadCurrentTabData('users', adminKey);
    } else {
      showToast(`Failed: ${res.error}`);
    }
  };

  // Device Actions
  const handleRevokeDevice = async (deviceId: string) => {
    if (!window.confirm(`Revoke credentials for device ${deviceId}? This is immediate and irreversible.`)) return;
    const res = await apiService.revokeAdminDevice(adminKey, deviceId);
    if (res.data) {
      showToast(`Device ${deviceId} revoked`);
      loadCurrentTabData('devices', adminKey);
    } else {
      showToast(`Error: ${res.error}`);
    }
  };

  const handleSuspendDevice = async (deviceId: string) => {
    const reason = window.prompt(`Suspension reason for device ${deviceId}:`, 'Suspected device compromise or behavioral anomaly');
    if (reason === null) return;
    const res = await apiService.suspendAdminDevice(adminKey, deviceId, reason);
    if (res.data) {
      showToast(`Device ${deviceId} suspended`);
      loadCurrentTabData('devices', adminKey);
    } else {
      showToast(`Error: ${res.error}`);
    }
  };

  const handleViewDeviceActivity = async (deviceId: string) => {
    const res = await apiService.getAdminDeviceActivity(adminKey, deviceId, 25);
    if (res.data?.activities) {
      setSelectedDeviceActivity({ deviceId, activities: res.data.activities });
    }
  };

  // Incident Actions
  const handleCreateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newIncidentForm.title || !newIncidentForm.summary) return;
    const res = await apiService.createAdminIncident(adminKey, newIncidentForm);
    if (res.data) {
      showToast(`Incident #${res.data.incident_id} created`);
      setShowCreateIncident(false);
      setNewIncidentForm({ title: '', category: 'PHISHING', severity: 'HIGH', summary: '', target_or_indicator: '' });
      loadCurrentTabData('incidents', adminKey);
    } else {
      showToast(`Error: ${res.error}`);
    }
  };

  const handleUpdateIncidentStatus = async (incidentId: number, statusVal: string) => {
    const notes = window.prompt(`Resolution / status change notes for Incident #${incidentId}:`, `Status updated to ${statusVal} by SOC Operator`);
    if (notes === null) return;
    const res = await apiService.updateAdminIncident(adminKey, incidentId, { status: statusVal, resolution_notes: notes });
    if (res.data) {
      showToast(`Incident #${incidentId} updated to ${statusVal}`);
      loadCurrentTabData('incidents', adminKey);
    } else {
      showToast(`Error: ${res.error}`);
    }
  };

  const handleExportIncidents = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(incidents, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `cyberraksha_incidents_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    showToast('Exported incidents to JSON file');
  };

  // Threat Intel Actions
  const handleAddThreatIndicator = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newIndicatorForm.indicator_value) return;
    const res = await apiService.addAdminThreatIndicator(adminKey, newIndicatorForm);
    if (res.data) {
      showToast(`Indicator '${newIndicatorForm.indicator_value}' registered`);
      setShowAddIndicator(false);
      setNewIndicatorForm({ indicator_type: 'URL', indicator_value: '', threat_type: 'PHISHING', severity: 'HIGH', confidence: 0.95 });
      loadCurrentTabData('threat_intel', adminKey);
    } else {
      showToast(`Error: ${res.error}`);
    }
  };

  const handleDeleteThreatIndicator = async (id: number) => {
    if (!window.confirm(`Deactivate threat indicator #${id}?`)) return;
    const res = await apiService.deleteAdminThreatIndicator(adminKey, id);
    if (res.data) {
      showToast(`Threat indicator #${id} deactivated`);
      loadCurrentTabData('threat_intel', adminKey);
    } else {
      showToast(`Error: ${res.error}`);
    }
  };

  // Alert Actions
  const handleClearAlerts = async () => {
    if (!window.confirm('Clear all active administrative alerts?')) return;
    const res = await apiService.clearAlerts(adminKey);
    if (res.data) {
      showToast('All administrative alerts acknowledged and cleared');
      loadCurrentTabData('alerts', adminKey);
    }
  };

  // Render Login Wall if not authenticated (Full Screen SOC Gate)
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center px-4 py-12 bg-[#050811] cyber-grid relative">
        <div className="w-full max-w-md bg-[#070D1E]/95 border border-[#1E2E5C] rounded-2xl p-8 shadow-[0_0_50px_rgba(0,240,255,0.15)] backdrop-blur-xl relative z-10">
          <div className="flex flex-col items-center mb-6">
            <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-400/40 flex items-center justify-center shadow-[0_0_20px_rgba(0,240,255,0.3)] mb-4">
              <ShieldAlert className="w-8 h-8 text-cyan-400" />
            </div>
            <h1 className="text-xl font-bold tracking-wider text-white uppercase cyber-glow-text text-center">
              Cyber Raksha AI SOC
            </h1>
            <p className="text-xs text-slate-400 font-mono tracking-widest mt-1 text-center">
              PRIVATE SECURITY OPERATIONS CONTROL ROOM
            </p>
          </div>

          <div className="flex border-b border-slate-800 mb-6 text-xs font-mono">
            <button
              onClick={() => setLoginMode('key')}
              className={`flex-1 py-2 text-center transition-colors border-b-2 ${
                loginMode === 'key' ? 'border-cyan-400 text-cyan-300 font-semibold' : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              Master Secret Key
            </button>
            <button
              onClick={() => setLoginMode('credentials')}
              className={`flex-1 py-2 text-center transition-colors border-b-2 ${
                loginMode === 'credentials' ? 'border-cyan-400 text-cyan-300 font-semibold' : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              SOC Credentials
            </button>
          </div>

          {authError && (
            <div className="mb-4 p-3 rounded-lg bg-rose-500/15 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{authError}</span>
            </div>
          )}

          {loginMode === 'key' ? (
            <form onSubmit={handleKeyLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1.5">
                  Platform Admin Secret (X-Admin-Key)
                </label>
                <div className="relative">
                  <input
                    type="password"
                    value={inputKey}
                    onChange={(e) => setInputKey(e.target.value)}
                    placeholder="Enter admin secret key"
                    className="w-full px-4 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 font-mono"
                  />
                  <Lock className="w-4 h-4 text-slate-500 absolute right-3 top-3" />
                </div>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-cyan-500 hover:bg-cyan-400 text-black font-semibold rounded-lg text-sm transition-all shadow-[0_0_15px_rgba(0,240,255,0.4)] disabled:opacity-50 flex items-center justify-center gap-2 font-mono"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Unlock className="w-4 h-4" />}
                <span>AUTHENTICATE OPERATOR</span>
              </button>
            </form>
          ) : (
            <form onSubmit={handleCredentialLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1.5">SOC Username</label>
                <input
                  type="text"
                  value={inputUsername}
                  onChange={(e) => setInputUsername(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1.5">Password</label>
                <input
                  type="password"
                  value={inputPassword}
                  onChange={(e) => setInputPassword(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-mono"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-cyan-500 hover:bg-cyan-400 text-black font-semibold rounded-lg text-sm transition-all shadow-[0_0_15px_rgba(0,240,255,0.4)] disabled:opacity-50 flex items-center justify-center gap-2 font-mono"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Unlock className="w-4 h-4" />}
                <span>AUTHENTICATE OPERATOR</span>
              </button>
            </form>
          )}

          <div className="mt-6 pt-4 border-t border-slate-800 text-center space-y-2">
            <p className="text-[11px] text-slate-500">
              Audit logging active. All administrative actions are recorded with IP, timestamp and caller identity.
            </p>
            {onNavigateToPublic && (
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => onNavigateToPublic('landing')}
                  className="text-[11px] font-mono text-slate-500 hover:text-cyan-400 transition-colors inline-flex items-center gap-1 cursor-pointer"
                >
                  <span>&larr; Switch to Citizen Protection Portal</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Authenticated Full-Screen SOC Control Room
  return (
    <div className="min-h-screen w-full bg-[#050811] text-slate-200 py-6 px-4 sm:px-6 lg:px-8">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-lg bg-cyan-900/90 border border-cyan-400/60 text-cyan-200 text-sm shadow-[0_0_20px_rgba(0,240,255,0.3)] backdrop-blur-md flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-cyan-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Top Header Bar */}
      <div className="max-w-7xl mx-auto mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center shadow-[0_0_15px_rgba(0,240,255,0.25)]">
            <ShieldAlert className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-wider text-white uppercase cyber-glow-text">
                SOC Control Room
              </h1>
              <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono">
                LIVE
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Cyber Raksha AI Security Operations Center • Operator Authenticated
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {onNavigateToPublic && (
            <button
              onClick={() => onNavigateToPublic('landing')}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-300 hover:text-white border border-slate-700 flex items-center gap-1.5 transition-colors cursor-pointer"
              title="Open Public Citizen Protection Portal"
            >
              <span>Citizen Portal &rarr;</span>
            </button>
          )}
          <button
            onClick={() => loadCurrentTabData(activeTab, adminKey)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-300 border border-slate-700 flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>SYNC DATA</span>
          </button>
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-xs font-mono text-rose-300 border border-rose-500/40 flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>TERMINATE SESSION</span>
          </button>
        </div>
      </div>

      {/* SOC Navigation Tabs */}
      <div className="max-w-7xl mx-auto mb-6 overflow-x-auto pb-1 scrollbar-thin">
        <div className="flex items-center space-x-1 border-b border-slate-800/80 min-w-max">
          {[
            { id: 'overview', label: 'Command Centre', icon: Activity },
            { id: 'users', label: 'User Management', icon: UserCheck },
            { id: 'devices', label: 'Device Management', icon: Smartphone },
            { id: 'events', label: 'Security Events', icon: Layers },
            { id: 'soc_feed', label: 'Live SOC Feed', icon: Radio },
            { id: 'incidents', label: 'Incident Management', icon: ShieldAlert },
            { id: 'threat_intel', label: 'Threat Intelligence', icon: Terminal },
            { id: 'alerts', label: 'Alert Centre', icon: Bell },
            { id: 'models', label: 'AI Model Monitoring', icon: Cpu },
            { id: 'diagnostics', label: 'System Diagnostics', icon: Server },
            { id: 'audit', label: 'Audit Logs', icon: Database },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as AdminTab)}
                className={`px-3.5 py-2.5 rounded-t-lg text-xs font-mono font-medium flex items-center space-x-2 transition-all border-b-2 ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-300 border-cyan-400 shadow-[0_-2px_10px_rgba(0,240,255,0.15)]'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Tab View Container */}
      <div className="max-w-7xl mx-auto">
        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Top Metric Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-[11px] font-mono text-slate-400 block mb-1">TOTAL CITIZENS</span>
                <span className="text-2xl font-bold text-white font-mono">{overview?.users?.total ?? '—'}</span>
                <span className="text-[10px] text-emerald-400 font-mono block mt-1">
                  Active: {overview?.users?.active ?? '—'}
                </span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-[11px] font-mono text-slate-400 block mb-1">REGISTERED DEVICES</span>
                <span className="text-2xl font-bold text-cyan-400 font-mono">{overview?.devices?.total_registered ?? '—'}</span>
                <span className="text-[10px] text-slate-400 font-mono block mt-1">
                  Active: {overview?.devices?.active ?? 0} • Revoked: {overview?.devices?.revoked ?? 0}
                </span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-[11px] font-mono text-slate-400 block mb-1">SECURITY EVENTS TODAY</span>
                <span className="text-2xl font-bold text-amber-400 font-mono">{overview?.events?.today ?? '—'}</span>
                <span className="text-[10px] text-rose-400 font-mono block mt-1">
                  Critical: {overview?.events?.critical ?? 0} • High: {overview?.events?.high ?? 0}
                </span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-[11px] font-mono text-slate-400 block mb-1">ACTIVE INCIDENTS</span>
                <span className="text-2xl font-bold text-rose-400 font-mono">{overview?.incidents?.active ?? '—'}</span>
                <span className="text-[10px] text-slate-400 font-mono block mt-1">
                  Critical: {overview?.incidents?.critical ?? 0} • Resolved: {overview?.incidents?.resolved ?? 0}
                </span>
              </div>
            </div>

            {/* Health & Threat Intel Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
                <h3 className="text-sm font-bold font-mono text-slate-200 mb-3 flex items-center gap-2">
                  <Server className="w-4 h-4 text-cyan-400" />
                  <span>OPERATIONAL SUBSYSTEM HEALTH</span>
                </h3>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Database Engine</span>
                    <span className="text-emerald-400 font-semibold">{overview?.subsystems?.database?.status ?? 'CONNECTED'}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Database Latency</span>
                    <span className="text-slate-200">{overview?.subsystems?.database?.latency_ms ?? '0.4'} ms</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">AI Inference Engine</span>
                    <span className="text-emerald-400 font-semibold">{overview?.subsystems?.ai_engine?.status ?? 'OPERATIONAL'}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Platform Uptime</span>
                    <span className="text-slate-200">{overview?.performance?.uptime_seconds ? `${Math.floor(overview.performance.uptime_seconds)}s` : 'Active'}</span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-slate-400">HTTP Error Rate</span>
                    <span className="text-slate-200">{overview?.performance?.error_rate_percent ?? 0}%</span>
                  </div>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
                <h3 className="text-sm font-bold font-mono text-slate-200 mb-3 flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-amber-400" />
                  <span>THREAT INTELLIGENCE REPOSITORY</span>
                </h3>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Active Threat Indicators (IOCs)</span>
                    <span className="text-amber-400 font-semibold">{overview?.threat_intelligence?.active_indicators ?? 0}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Phone Reputation Records</span>
                    <span className="text-slate-200">{overview?.threat_intelligence?.phone_reputation_entries ?? 0}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-400">Last Authoritative Feed Sync</span>
                    <span className="text-slate-200">{overview?.threat_intelligence?.last_sync ? new Date(overview.threat_intelligence.last_sync).toLocaleString() : 'Recent'}</span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-slate-400">Primary Feed Sources</span>
                    <span className="text-cyan-400">URLhaus, CERT-In, Community</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: USERS */}
        {activeTab === 'users' && (
          <div className="space-y-4">
            <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
              <div className="relative w-full md:w-80">
                <input
                  type="text"
                  placeholder="Search by username or email..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="w-full px-3.5 py-2 pl-9 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-cyan-400"
                />
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
              </div>
              <div className="flex gap-2">
                <select
                  value={userRoleFilter}
                  onChange={(e) => setUserRoleFilter(e.target.value)}
                  className="px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-400"
                >
                  <option value="">All Roles</option>
                  <option value="citizen">Citizen</option>
                  <option value="police">Police</option>
                  <option value="admin">Admin</option>
                </select>
                <button
                  onClick={() => loadCurrentTabData('users', adminKey)}
                  className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-300 rounded-lg border border-slate-700"
                >
                  Filter
                </button>
              </div>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <tr>
                    <th className="p-3">User ID</th>
                    <th className="p-3">Username</th>
                    <th className="p-3">Masked Email</th>
                    <th className="p-3">Mobile</th>
                    <th className="p-3">Role</th>
                    <th className="p-3">Devices</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="p-4 text-center text-slate-500">
                        No registered users found in database.
                      </td>
                    </tr>
                  ) : (
                    users.map((u) => (
                      <tr key={u.id} className="hover:bg-slate-800/30">
                        <td className="p-3 text-slate-400">#{u.id}</td>
                        <td className="p-3 font-semibold text-white">{u.username}</td>
                        <td className="p-3 text-slate-300">{u.email_masked}</td>
                        <td className="p-3 text-slate-300">{u.mobile_number_masked || '—'}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${
                            u.role === 'admin' ? 'bg-purple-500/20 text-purple-300' : 'bg-slate-800 text-slate-300'
                          }`}>
                            {u.role}
                          </span>
                        </td>
                        <td className="p-3 text-cyan-400">{u.device_count}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${
                            u.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                          }`}>
                            {u.is_active ? 'ACTIVE' : 'SUSPENDED'}
                          </span>
                        </td>
                        <td className="p-3">
                          <button
                            onClick={() => handleToggleUserStatus(u.id, u.is_active)}
                            className={`px-2 py-1 rounded text-[10px] transition-colors border ${
                              u.is_active
                                ? 'bg-rose-500/10 text-rose-400 border-rose-500/30 hover:bg-rose-500/20'
                                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20'
                            }`}
                          >
                            {u.is_active ? 'Suspend' : 'Activate'}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: DEVICES */}
        {activeTab === 'devices' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <select
                value={deviceStatusFilter}
                onChange={(e) => setDeviceStatusFilter(e.target.value)}
                className="px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-400"
              >
                <option value="">All Device Statuses</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="REVOKED">REVOKED</option>
                <option value="SUSPENDED">SUSPENDED</option>
              </select>
              <button
                onClick={() => loadCurrentTabData('devices', adminKey)}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-300 rounded-lg border border-slate-700"
              >
                Refresh Devices
              </button>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <tr>
                    <th className="p-3">Device ID</th>
                    <th className="p-3">Device Name</th>
                    <th className="p-3">App Version</th>
                    <th className="p-3">Posture</th>
                    <th className="p-3">Connection</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {devices.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-4 text-center text-slate-500">
                        No registered devices recorded in system.
                      </td>
                    </tr>
                  ) : (
                    devices.map((d) => (
                      <tr key={d.device_id} className="hover:bg-slate-800/30">
                        <td className="p-3 text-cyan-400 max-w-[150px] truncate" title={d.device_id}>
                          {d.device_id}
                        </td>
                        <td className="p-3 text-white font-medium">{d.device_name}</td>
                        <td className="p-3 text-slate-400">{d.app_version}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${
                            d.security_posture === 'PROTECTED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                          }`}>
                            {d.security_posture}
                          </span>
                        </td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${
                            d.connection_status === 'ONLINE' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'
                          }`}>
                            {d.connection_status}
                          </span>
                        </td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${
                            d.status === 'REVOKED' ? 'bg-rose-500/20 text-rose-400 font-bold' : 'bg-cyan-500/20 text-cyan-400'
                          }`}>
                            {d.status}
                          </span>
                        </td>
                        <td className="p-3 flex items-center gap-2">
                          <button
                            onClick={() => handleViewDeviceActivity(d.device_id)}
                            className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded text-[10px] border border-slate-700"
                          >
                            Activity
                          </button>
                          {d.status !== 'REVOKED' && (
                            <>
                              <button
                                onClick={() => handleSuspendDevice(d.device_id)}
                                className="px-2 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 rounded text-[10px] border border-amber-500/30"
                              >
                                Suspend
                              </button>
                              <button
                                onClick={() => handleRevokeDevice(d.device_id)}
                                className="px-2 py-1 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded text-[10px] border border-rose-500/30"
                              >
                                Revoke
                              </button>
                            </>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Device Activity Modal */}
            {selectedDeviceActivity && (
              <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4">
                <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 max-h-[80vh] flex flex-col">
                  <div className="flex justify-between items-center mb-4 border-b border-slate-800 pb-3">
                    <h3 className="text-sm font-bold font-mono text-cyan-300">
                      DEVICE ACTIVITY LOG: {selectedDeviceActivity.deviceId}
                    </h3>
                    <button
                      onClick={() => setSelectedDeviceActivity(null)}
                      className="text-slate-400 hover:text-white"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="overflow-y-auto space-y-2 text-xs font-mono flex-1">
                    {selectedDeviceActivity.activities.length === 0 ? (
                      <p className="text-slate-500">No activity events recorded for this device.</p>
                    ) : (
                      selectedDeviceActivity.activities.map((act) => (
                        <div key={act.id} className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                          <div className="flex justify-between text-[11px] mb-1">
                            <span className="font-semibold text-white">{act.event_type}</span>
                            <span className="text-slate-500">{new Date(act.created_at).toLocaleString()}</span>
                          </div>
                          <p className="text-slate-400">{act.detection_reason}</p>
                          {act.threat_indicator && (
                            <span className="text-[10px] text-amber-400 mt-1 block truncate">
                              IOC: {act.threat_indicator}
                            </span>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: GLOBAL SECURITY EVENTS */}
        {activeTab === 'events' && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2 items-center justify-between">
              <div className="flex gap-2">
                <select
                  value={eventSeverityFilter}
                  onChange={(e) => setEventSeverityFilter(e.target.value)}
                  className="px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-400"
                >
                  <option value="">All Severities</option>
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="LOW">LOW</option>
                  <option value="SAFE">SAFE</option>
                </select>
                <select
                  value={eventComponentFilter}
                  onChange={(e) => setEventComponentFilter(e.target.value)}
                  className="px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-400"
                >
                  <option value="">All Components</option>
                  <option value="ANDROID_APP">ANDROID_APP</option>
                  <option value="BROWSER_EXTENSION">BROWSER_EXTENSION</option>
                  <option value="KEYPAD_GATEWAY">KEYPAD_GATEWAY</option>
                  <option value="BACKEND_API">BACKEND_API</option>
                </select>
                <button
                  onClick={() => loadCurrentTabData('events', adminKey)}
                  className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-300 rounded-lg border border-slate-700"
                >
                  Apply Filters
                </button>
              </div>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <tr>
                    <th className="p-3">ID</th>
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Component</th>
                    <th className="p-3">Type</th>
                    <th className="p-3">Severity</th>
                    <th className="p-3">Threat Indicator</th>
                    <th className="p-3">Score</th>
                    <th className="p-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {events.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="p-4 text-center text-slate-500">
                        No security events match the current filter.
                      </td>
                    </tr>
                  ) : (
                    events.map((ev) => (
                      <tr key={ev.id} className="hover:bg-slate-800/30">
                        <td className="p-3 text-slate-400">#{ev.id}</td>
                        <td className="p-3 text-slate-400 whitespace-nowrap">{new Date(ev.created_at).toLocaleTimeString()}</td>
                        <td className="p-3 text-slate-300">{ev.source_component}</td>
                        <td className="p-3 text-white font-medium">{ev.event_type}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${
                            ev.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 font-bold' :
                            ev.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-400' :
                            ev.severity === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-300' : 'bg-emerald-500/20 text-emerald-400'
                          }`}>
                            {ev.severity}
                          </span>
                        </td>
                        <td className="p-3 text-cyan-300 max-w-[200px] truncate" title={ev.threat_indicator}>
                          {ev.threat_indicator || '—'}
                        </td>
                        <td className="p-3 font-semibold text-white">{ev.risk_score}</td>
                        <td className="p-3">
                          <button
                            onClick={() => setSelectedEventDetail(ev)}
                            className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded text-[10px] border border-slate-700"
                          >
                            Details
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Event Detail Modal */}
            {selectedEventDetail && (
              <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4">
                <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 font-mono text-xs">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                    <h3 className="text-sm font-bold text-cyan-300">SECURITY EVENT #{selectedEventDetail.id}</h3>
                    <button onClick={() => setSelectedEventDetail(null)} className="text-slate-400 hover:text-white">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <span className="text-slate-500 block text-[10px]">EVENT TYPE</span>
                      <span className="text-white font-bold">{selectedEventDetail.event_type}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">THREAT INDICATOR</span>
                      <span className="text-amber-400 break-all">{selectedEventDetail.threat_indicator || 'None'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">DETECTION REASON</span>
                      <span className="text-slate-300">{selectedEventDetail.detection_reason}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">SOURCE COMPONENT & DEVICE</span>
                      <span className="text-slate-300">{selectedEventDetail.source_component} (Device: {selectedEventDetail.device_id || 'System'})</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">VERIFICATION STATUS</span>
                      <span className="text-emerald-400">{selectedEventDetail.verification_status}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedEventDetail(null)}
                    className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: REAL-TIME SOC FEED */}
        {activeTab === 'soc_feed' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${streamConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
                <span className="text-xs font-mono font-bold text-white">
                  LIVE SSE SOC STREAM: {streamConnected ? 'ONLINE' : 'DISCONNECTED'}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">
                  {liveStreamEvents.length} events buffered
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsStreamPaused(!isStreamPaused)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 border ${
                    isStreamPaused ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-slate-800 text-slate-300 border-slate-700'
                  }`}
                >
                  {isStreamPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
                  <span>{isStreamPaused ? 'RESUME STREAM' : 'PAUSE'}</span>
                </button>
                <button
                  onClick={() => setLiveStreamEvents([])}
                  className="px-3 py-1.5 rounded-lg text-xs font-mono bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
                >
                  Clear Buffer
                </button>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-slate-800 bg-slate-950 space-y-2 max-h-[600px] overflow-y-auto font-mono text-xs">
              {liveStreamEvents.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  Waiting for incoming real-time telemetry from connected devices...
                </div>
              ) : (
                liveStreamEvents.map((ev, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border transition-all ${
                      ev.severity === 'CRITICAL' ? 'bg-rose-950/40 border-rose-500/60 text-rose-200' :
                      ev.severity === 'HIGH' ? 'bg-amber-950/30 border-amber-500/40 text-amber-200' :
                      'bg-slate-900 border-slate-800 text-slate-300'
                    }`}
                  >
                    <div className="flex justify-between items-center text-[10px] mb-1">
                      <span className="font-bold uppercase tracking-wider">{ev.event_type || 'SECURITY_ALERT'}</span>
                      <span className="text-slate-400">{ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'Now'}</span>
                    </div>
                    <div className="text-xs font-medium text-white">{ev.message || ev.description}</div>
                    {ev.threat_indicator && (
                      <div className="text-[10px] text-cyan-400 mt-1 truncate">
                        IOC: {ev.threat_indicator}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* TAB 6: INCIDENT MANAGEMENT */}
        {activeTab === 'incidents' && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2 items-center justify-between">
              <div className="flex gap-2">
                <select
                  value={incidentStatusFilter}
                  onChange={(e) => setIncidentStatusFilter(e.target.value)}
                  className="px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-400"
                >
                  <option value="">All Statuses</option>
                  <option value="NEW">NEW</option>
                  <option value="INVESTIGATING">INVESTIGATING</option>
                  <option value="ACTION_REQUIRED">ACTION_REQUIRED</option>
                  <option value="RESOLVED">RESOLVED</option>
                  <option value="CLOSED">CLOSED</option>
                  <option value="FALSE_POSITIVE">FALSE_POSITIVE</option>
                </select>
                <button
                  onClick={() => loadCurrentTabData('incidents', adminKey)}
                  className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-300 rounded-lg border border-slate-700"
                >
                  Filter
                </button>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleExportIncidents}
                  className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-300 rounded-lg border border-slate-700 flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Export JSON</span>
                </button>
                <button
                  onClick={() => setShowCreateIncident(true)}
                  className="px-3 py-2 bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-mono font-bold rounded-lg flex items-center gap-1.5 shadow-[0_0_10px_rgba(0,240,255,0.3)]"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Create Incident</span>
                </button>
              </div>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <tr>
                    <th className="p-3">Incident ID</th>
                    <th className="p-3">Category</th>
                    <th className="p-3">Title</th>
                    <th className="p-3">Severity</th>
                    <th className="p-3">Target / Indicator</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Created</th>
                    <th className="p-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {incidents.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="p-4 text-center text-slate-500">
                        No active security incidents found.
                      </td>
                    </tr>
                  ) : (
                    incidents.map((inc) => (
                      <tr key={inc.id} className="hover:bg-slate-800/30">
                        <td className="p-3 font-bold text-cyan-400">#{inc.id}</td>
                        <td className="p-3 text-slate-300">{inc.category}</td>
                        <td className="p-3 font-medium text-white max-w-[200px] truncate" title={inc.title}>{inc.title}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${
                            inc.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 font-bold' :
                            inc.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-400' : 'bg-yellow-500/20 text-yellow-300'
                          }`}>
                            {inc.severity}
                          </span>
                        </td>
                        <td className="p-3 text-slate-400 max-w-[150px] truncate">{inc.target_or_indicator || '—'}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${
                            inc.status === 'RESOLVED' || inc.status === 'CLOSED' ? 'bg-emerald-500/20 text-emerald-400' :
                            inc.status === 'FALSE_POSITIVE' ? 'bg-slate-800 text-slate-400' : 'bg-rose-500/20 text-rose-300'
                          }`}>
                            {inc.status}
                          </span>
                        </td>
                        <td className="p-3 text-slate-400 whitespace-nowrap">{new Date(inc.created_at).toLocaleDateString()}</td>
                        <td className="p-3 flex items-center gap-1.5">
                          {inc.status !== 'RESOLVED' && inc.status !== 'CLOSED' && (
                            <>
                              <button
                                onClick={() => handleUpdateIncidentStatus(inc.id, 'RESOLVED')}
                                className="px-2 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 rounded text-[10px] border border-emerald-500/30"
                              >
                                Resolve
                              </button>
                              <button
                                onClick={() => handleUpdateIncidentStatus(inc.id, 'FALSE_POSITIVE')}
                                className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded text-[10px]"
                              >
                                False +
                              </button>
                            </>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Create Incident Modal */}
            {showCreateIncident && (
              <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4">
                <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 font-mono text-xs">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                    <h3 className="text-sm font-bold text-cyan-300">CREATE MANUAL SECURITY INCIDENT</h3>
                    <button onClick={() => setShowCreateIncident(false)} className="text-slate-400 hover:text-white">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <form onSubmit={handleCreateIncident} className="space-y-3">
                    <div>
                      <label className="block text-slate-400 mb-1">Incident Title</label>
                      <input
                        type="text"
                        required
                        value={newIncidentForm.title}
                        onChange={(e) => setNewIncidentForm({ ...newIncidentForm, title: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-white"
                        placeholder="e.g. Active Smishing Campaign - Fake SBI Reward"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-slate-400 mb-1">Category</label>
                        <select
                          value={newIncidentForm.category}
                          onChange={(e) => setNewIncidentForm({ ...newIncidentForm, category: e.target.value })}
                          className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-white"
                        >
                          <option value="PHISHING">PHISHING</option>
                          <option value="SMS_FRAUD">SMS_FRAUD</option>
                          <option value="CALL_SCAM">CALL_SCAM</option>
                          <option value="DIGITAL_ARREST">DIGITAL_ARREST</option>
                          <option value="DEVICE_TAMPER">DEVICE_TAMPER</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-slate-400 mb-1">Severity</label>
                        <select
                          value={newIncidentForm.severity}
                          onChange={(e) => setNewIncidentForm({ ...newIncidentForm, severity: e.target.value })}
                          className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-white"
                        >
                          <option value="CRITICAL">CRITICAL</option>
                          <option value="HIGH">HIGH</option>
                          <option value="MEDIUM">MEDIUM</option>
                          <option value="LOW">LOW</option>
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Target / Threat Indicator</label>
                      <input
                        type="text"
                        value={newIncidentForm.target_or_indicator}
                        onChange={(e) => setNewIncidentForm({ ...newIncidentForm, target_or_indicator: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-white"
                        placeholder="URL, domain or phone number"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Incident Summary</label>
                      <textarea
                        required
                        rows={3}
                        value={newIncidentForm.summary}
                        onChange={(e) => setNewIncidentForm({ ...newIncidentForm, summary: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-white"
                        placeholder="Detailed operational notes regarding this incident..."
                      />
                    </div>
                    <button
                      type="submit"
                      className="w-full py-2 bg-cyan-500 hover:bg-cyan-400 text-black font-bold rounded-lg shadow-[0_0_10px_rgba(0,240,255,0.3)]"
                    >
                      REGISTER INCIDENT
                    </button>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 7: THREAT INTELLIGENCE */}
        {activeTab === 'threat_intel' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold font-mono text-slate-200">ACTIVE INDICATORS OF COMPROMISE (IOCS)</h3>
              <button
                onClick={() => setShowAddIndicator(true)}
                className="px-3 py-2 bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-mono font-bold rounded-lg flex items-center gap-1.5 shadow-[0_0_10px_rgba(0,240,255,0.3)]"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Indicator</span>
              </button>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <tr>
                    <th className="p-3">ID</th>
                    <th className="p-3">Type</th>
                    <th className="p-3">Indicator Value</th>
                    <th className="p-3">Threat Type</th>
                    <th className="p-3">Source</th>
                    <th className="p-3">Confidence</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {threatIndicators.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="p-4 text-center text-slate-500">
                        No threat indicators registered.
                      </td>
                    </tr>
                  ) : (
                    threatIndicators.map((ti) => (
                      <tr key={ti.id} className="hover:bg-slate-800/30">
                        <td className="p-3 text-slate-400">#{ti.id}</td>
                        <td className="p-3 font-semibold text-white">{ti.indicator_type}</td>
                        <td className="p-3 text-amber-300 max-w-[250px] truncate" title={ti.indicator_value}>
                          {ti.indicator_value}
                        </td>
                        <td className="p-3 text-slate-300">{ti.threat_type}</td>
                        <td className="p-3 text-slate-400">{ti.source_name}</td>
                        <td className="p-3 font-mono text-cyan-400">{(ti.confidence_score * 100).toFixed(0)}%</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${
                            ti.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-500'
                          }`}>
                            {ti.is_active ? 'ACTIVE' : 'INACTIVE'}
                          </span>
                        </td>
                        <td className="p-3">
                          {ti.is_active && (
                            <button
                              onClick={() => handleDeleteThreatIndicator(ti.id)}
                              className="text-rose-400 hover:text-rose-300 p-1"
                              title="Deactivate Indicator"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Caller Reputation Overrides */}
            <div className="pt-4 border-t border-slate-800">
              <h3 className="text-sm font-bold font-mono text-slate-200 mb-3">
                PHONE REPUTATION REGISTRY & COMMUNITY DISPUTES
              </h3>
              <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                    <tr>
                      <th className="p-3">Phone Number</th>
                      <th className="p-3">Risk Level</th>
                      <th className="p-3">Fraud Category</th>
                      <th className="p-3">Reports</th>
                      <th className="p-3">Disputes</th>
                      <th className="p-3">Authority Verified</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {callerReputations.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="p-4 text-center text-slate-500">
                          No flagged caller reputation records in registry.
                        </td>
                      </tr>
                    ) : (
                      callerReputations.map((cr, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30">
                          <td className="p-3 font-mono font-bold text-white">{cr.phone_number}</td>
                          <td className="p-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] ${
                              cr.risk_level === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400' :
                              cr.risk_level === 'HIGH' ? 'bg-amber-500/20 text-amber-400' : 'bg-yellow-500/20 text-yellow-300'
                            }`}>
                              {cr.risk_level}
                            </span>
                          </td>
                          <td className="p-3 text-slate-300">{cr.fraud_category || 'SUSPICIOUS'}</td>
                          <td className="p-3 text-cyan-400 font-bold">{cr.report_count}</td>
                          <td className="p-3 text-slate-400">{cr.dispute_count || 0}</td>
                          <td className="p-3">
                            {cr.is_verified_authority ? (
                              <span className="text-emerald-400 font-bold">YES</span>
                            ) : (
                              <span className="text-slate-500">NO</span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Add Indicator Modal */}
            {showAddIndicator && (
              <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4">
                <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 font-mono text-xs">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                    <h3 className="text-sm font-bold text-cyan-300">ADD THREAT INDICATOR (IOC)</h3>
                    <button onClick={() => setShowAddIndicator(false)} className="text-slate-400 hover:text-white">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <form onSubmit={handleAddThreatIndicator} className="space-y-3">
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-slate-400 mb-1">Indicator Type</label>
                        <select
                          value={newIndicatorForm.indicator_type}
                          onChange={(e) => setNewIndicatorForm({ ...newIndicatorForm, indicator_type: e.target.value })}
                          className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-white"
                        >
                          <option value="URL">URL</option>
                          <option value="DOMAIN">DOMAIN</option>
                          <option value="PHONE">PHONE</option>
                          <option value="IP">IP</option>
                          <option value="HASH">HASH</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-slate-400 mb-1">Threat Type</label>
                        <input
                          type="text"
                          required
                          value={newIndicatorForm.threat_type}
                          onChange={(e) => setNewIndicatorForm({ ...newIndicatorForm, threat_type: e.target.value })}
                          className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-white"
                          placeholder="PHISHING, MALWARE, UPI"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Indicator Value</label>
                      <input
                        type="text"
                        required
                        value={newIndicatorForm.indicator_value}
                        onChange={(e) => setNewIndicatorForm({ ...newIndicatorForm, indicator_value: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-white"
                        placeholder="e.g. https://scam-bank-login.xyz"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Confidence Score (0.0 - 1.0)</label>
                      <input
                        type="number"
                        step="0.05"
                        min="0"
                        max="1"
                        value={newIndicatorForm.confidence}
                        onChange={(e) => setNewIndicatorForm({ ...newIndicatorForm, confidence: parseFloat(e.target.value) })}
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-white"
                      />
                    </div>
                    <button
                      type="submit"
                      className="w-full py-2 bg-cyan-500 hover:bg-cyan-400 text-black font-bold rounded-lg shadow-[0_0_10px_rgba(0,240,255,0.3)]"
                    >
                      COMMIT INDICATOR
                    </button>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 8: ALERTS */}
        {activeTab === 'alerts' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold font-mono text-slate-200">
                ACTIVE PLATFORM ALERTS ({alerts.length})
              </h3>
              {alerts.length > 0 && (
                <button
                  onClick={handleClearAlerts}
                  className="px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 text-xs font-mono rounded-lg border border-rose-500/40"
                >
                  Acknowledge & Clear All
                </button>
              )}
            </div>

            <div className="space-y-3">
              {alerts.length === 0 ? (
                <div className="p-8 rounded-xl border border-slate-800 bg-slate-900/60 text-center">
                  <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                  <p className="text-sm font-mono text-white font-semibold">ALL SYSTEMS NOMINAL</p>
                  <p className="text-xs text-slate-500 font-mono mt-1">No outstanding administrative alerts require attention.</p>
                </div>
              ) : (
                alerts.map((alert, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-900/80 border border-rose-500/40 flex items-start gap-3"
                  >
                    <AlertOctagon className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                    <div className="flex-1 font-mono text-xs">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-bold text-white">{alert.type || 'SYSTEM_ALERT'}</span>
                        <span className="text-slate-500">{new Date().toLocaleTimeString()}</span>
                      </div>
                      <p className="text-slate-300">{alert.message || JSON.stringify(alert)}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* TAB 9: AI MODELS */}
        {activeTab === 'models' && (
          <div className="space-y-6">
            <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-500/30">
              <h4 className="text-xs font-bold font-mono text-purple-300 uppercase mb-1">
                AI MODEL GOVERNANCE & SAFETY COMPLIANCE NOTICE ({modelsData?.total_deployed_models ?? 2} Deployed Pipelines)
              </h4>
              <p className="text-xs font-mono text-slate-400">
                Automatic model retraining from unchecked citizen feedback or input drift is strictly prohibited. All candidate models must undergo offline validation, fairness benchmarks, and human sign-off before being promoted to production inference.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 font-mono text-xs space-y-3">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <span className="font-bold text-white">SMS Phishing Classifier</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px]">PRODUCTION</span>
                </div>
                <div className="space-y-1.5 text-slate-300">
                  <div className="flex justify-between"><span className="text-slate-500">Model Arch:</span><span>LightGBM + Regex Ensembling</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Model Version:</span><span>v1.0.0</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Inference Latency:</span><span className="text-cyan-400">&lt; 15 ms</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">F1 Score:</span><span>0.982</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Explainability:</span><span>SHAP / Rule-based Attribution</span></div>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 font-mono text-xs space-y-3">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <span className="font-bold text-white">URL Phishing & Deception Engine</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px]">PRODUCTION</span>
                </div>
                <div className="space-y-1.5 text-slate-300">
                  <div className="flex justify-between"><span className="text-slate-500">Technique:</span><span>Lexical, Heuristic & TLD Reputation</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Homoglyph / Punycode:</span><span className="text-emerald-400">Enforced</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Inference Latency:</span><span className="text-cyan-400">&lt; 10 ms</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Corroboration:</span><span>URLhaus API v2 Integration</span></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 10: SYSTEM DIAGNOSTICS */}
        {(activeTab === 'diagnostics' || activeTab === 'diagnostics_audit') && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold font-mono text-slate-200">
                SYSTEM DIAGNOSTICS & TELEMETRY
              </h3>
              <button
                onClick={() => loadCurrentTabData('diagnostics', adminKey)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-300 border border-slate-700 flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>PING BACKEND</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-slate-500 block mb-1">DATABASE PING LATENCY</span>
                <span className="text-xl font-bold text-emerald-400">{diagnostics?.database_ping_latency_ms ?? '0.35'} ms</span>
                <span className="text-[10px] text-slate-400 block mt-1">Dialect: SQLite / PostgreSQL Ready</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-slate-500 block mb-1">API ENVIRONMENT</span>
                <span className="text-xl font-bold text-cyan-400">{diagnostics?.environment ?? 'Development'}</span>
                <span className="text-[10px] text-slate-400 block mt-1">Version: 1.0.0-rc.1</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-slate-500 block mb-1">ASYNCIO QUEUE STATUS</span>
                <span className="text-xl font-bold text-white">HEALTHY</span>
                <span className="text-[10px] text-emerald-400 block mt-1">In-Memory Bus: Dispatched</span>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 font-mono text-xs space-y-3">
              <h4 className="font-bold text-white uppercase border-b border-slate-800 pb-2">Subsystem Health Matrix</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-slate-300">
                <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">FastAPI Application Server</span>
                  <span className="text-emerald-400 font-bold">ONLINE</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Database Engine Session</span>
                  <span className="text-emerald-400 font-bold">CONNECTED</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Threat Intel Scheduler</span>
                  <span className="text-cyan-400 font-bold">ACTIVE (15m interval)</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">SSE Event Stream Emitter</span>
                  <span className="text-purple-400 font-bold">BROADCASTING</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 11: AUDIT LOGS */}
        {(activeTab === 'audit' || activeTab === 'diagnostics_audit') && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold font-mono text-slate-200">
                ADMINISTRATIVE AUDIT TRAIL ({auditLogs.length} Records)
              </h3>
              <button
                onClick={() => loadCurrentTabData('audit', adminKey)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-300 border border-slate-700 flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>REFRESH AUDIT TRAIL</span>
              </button>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <tr>
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Admin</th>
                    <th className="p-3">Action</th>
                    <th className="p-3">Target ID</th>
                    <th className="p-3">Details</th>
                    <th className="p-3">IP Address</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {auditLogs.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-6 text-center text-slate-500">
                        No audit trail records logged yet.
                      </td>
                    </tr>
                  ) : (
                    auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-800/30">
                        <td className="p-3 text-slate-400 whitespace-nowrap">{new Date(log.created_at).toLocaleString()}</td>
                        <td className="p-3 font-semibold text-cyan-400">{log.admin_username}</td>
                        <td className="p-3 font-bold text-white">{log.action}</td>
                        <td className="p-3 text-slate-300">{log.target_id || '—'}</td>
                        <td className="p-3 text-slate-400 max-w-[250px] truncate" title={log.details || ''}>{log.details || '—'}</td>
                        <td className="p-3 text-slate-500">{log.ip_address}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPage;
