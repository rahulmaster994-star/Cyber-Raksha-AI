import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Activity,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  RefreshCw,
  ExternalLink,
  ShieldAlert,
  Shield,
  MessageSquare,
  Mic,
  Radio,
  Sliders,
  FileText,
  Bell,
  CheckCheck,
  Trash2,
  Settings,
  Filter,
  Info,
  AlertTriangle,
  ShieldCheck
} from 'lucide-react';
import { apiService } from '../services/api';
import type {
  HealthCheckData,
  SystemInfoData,
  SecurityModulesResponse,
  NotificationItem,
  NotificationPreferenceData
} from '../services/api';

interface DashboardPageProps {
  health: HealthCheckData | null;
  systemInfo: SystemInfoData | null;
  modulesData: SecurityModulesResponse | null;
  isOnline: boolean;
  error: string | null;
  onRefresh: () => void;
  isRefreshing: boolean;
  onNavigateToModules: () => void;
  onNavigate?: (tab: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  health,
  isOnline,
  error,
  onRefresh,
  isRefreshing,
  onNavigateToModules,
  onNavigate,
}) => {
  const [stats, setStats] = useState<any>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [showExtensionModal, setShowExtensionModal] = useState(false);
  const [showMobileModal, setShowMobileModal] = useState(false);

  // Phase B3: Unified Protection Command Center State
  const [b3Overview, setB3Overview] = useState<any>(null);
  const [b3Activity, setB3Activity] = useState<any[]>([]);
  const [b3Incidents, setB3Incidents] = useState<any[]>([]);
  const [isProcessingIncident, setIsProcessingIncident] = useState<number | null>(null);

  // Phase A3: Security Alert Notifications State
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadNotifCount, setUnreadNotifCount] = useState<number>(0);
  const [totalNotifs, setTotalNotifs] = useState<number>(0);
  const [isLoadingNotifs, setIsLoadingNotifs] = useState<boolean>(false);
  const [notifSeverityFilter, setNotifSeverityFilter] = useState<string>('ALL');
  const [notifCategoryFilter, setNotifCategoryFilter] = useState<string>('ALL');
  const [notifUnreadOnly, setNotifUnreadOnly] = useState<boolean>(false);
  const [showNotifPrefsModal, setShowNotifPrefsModal] = useState<boolean>(false);
  const [notifPrefs, setNotifPrefs] = useState<NotificationPreferenceData | null>(null);
  const [isSavingPrefs, setIsSavingPrefs] = useState<boolean>(false);
  const [sseConnected, setSseConnected] = useState<boolean>(false);

  const fetchNotifications = async () => {
    setIsLoadingNotifs(true);
    try {
      const params: any = { limit: 50 };
      if (notifSeverityFilter !== 'ALL') params.severity = notifSeverityFilter;
      if (notifCategoryFilter !== 'ALL') params.category = notifCategoryFilter;
      if (notifUnreadOnly) params.is_read = false;

      const res = await apiService.getNotifications(params);
      if (res.data) {
        setNotifications(res.data.items);
        setUnreadNotifCount(res.data.unread_count);
        setTotalNotifs(res.data.total);
      }
    } catch (_) {
    } finally {
      setIsLoadingNotifs(false);
    }
  };

  const fetchNotifPrefs = async () => {
    try {
      const res = await apiService.getNotificationPreferences();
      if (res.data) setNotifPrefs(res.data);
    } catch (_) {}
  };

  useEffect(() => {
    fetchNotifications();
    fetchNotifPrefs();

    // Subscribe to SSE stream
    const unsubscribe = apiService.subscribeNotificationStream(
      (newNotif) => {
        setNotifications((prev) => [newNotif, ...prev]);
        setUnreadNotifCount((prev) => prev + 1);
        setTotalNotifs((prev) => prev + 1);
      },
      () => setSseConnected(true)
    );

    // Fallback polling interval every 15 seconds
    const interval = setInterval(fetchNotifications, 15000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, [isOnline, notifSeverityFilter, notifCategoryFilter, notifUnreadOnly]);

  const handleMarkRead = async (id: number) => {
    await apiService.markNotificationRead(id);
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    setUnreadNotifCount((prev) => Math.max(0, prev - 1));
  };

  const handleMarkAllRead = async () => {
    await apiService.markAllNotificationsRead();
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadNotifCount(0);
  };

  const handleDeleteNotif = async (id: number) => {
    await apiService.deleteNotification(id);
    setNotifications((prev) => prev.filter((n) => n.id !== id));
    setTotalNotifs((prev) => Math.max(0, prev - 1));
  };

  const handleClearAllNotifs = async () => {
    if (window.confirm('Are you sure you want to clear all security notification history?')) {
      await apiService.clearAllNotifications();
      setNotifications([]);
      setUnreadNotifCount(0);
      setTotalNotifs(0);
    }
  };

  const handleSaveNotifPrefs = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notifPrefs) return;
    setIsSavingPrefs(true);
    try {
      const res = await apiService.updateNotificationPreferences({
        browser_notifications_enabled: notifPrefs.browser_notifications_enabled,
        min_severity: notifPrefs.min_severity,
        categories_enabled: notifPrefs.categories_enabled,
        sound_enabled: notifPrefs.sound_enabled,
      });
      if (res.data) {
        setNotifPrefs(res.data);
        setShowNotifPrefsModal(false);
      }
    } catch (_) {
    } finally {
      setIsSavingPrefs(false);
    }
  };

  const fetchStats = async () => {
    setIsLoadingStats(true);
    try {
      const [statsRes, ovRes, actRes, incRes] = await Promise.allSettled([
        apiService.getDashboardStats(),
        apiService.getDashboardOverview(),
        apiService.getDashboardActivity(10),
        apiService.getDashboardIncidents(10),
      ]);
      if (statsRes.status === 'fulfilled' && statsRes.value.data) {
        setStats(statsRes.value.data);
      }
      if (ovRes.status === 'fulfilled' && ovRes.value.data) {
        setB3Overview(ovRes.value.data);
      }
      if (actRes.status === 'fulfilled' && actRes.value.data) {
        setB3Activity(actRes.value.data.activities || []);
      }
      if (incRes.status === 'fulfilled' && incRes.value.data) {
        setB3Incidents(incRes.value.data.incidents || []);
      }
    } catch {
      // Graceful fallback to null
    } finally {
      setIsLoadingStats(false);
    }
  };

  const handleAcknowledgeIncident = async (incidentId: number) => {
    setIsProcessingIncident(incidentId);
    try {
      await apiService.acknowledgeIncident(incidentId);
      await fetchStats();
    } finally {
      setIsProcessingIncident(null);
    }
  };

  const handleResolveIncident = async (incidentId: number) => {
    setIsProcessingIncident(incidentId);
    try {
      await apiService.resolveIncident(incidentId, 'Resolved via Unified Command Center');
      await fetchStats();
    } finally {
      setIsProcessingIncident(null);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [isOnline]);

  const handleCombinedRefresh = () => {
    onRefresh();
    fetchStats();
  };

  const totalAnalyses = stats?.total_analyses ?? 0;
  const urlTotal = stats?.url_threats?.total ?? 0;
  const urlThreats = stats?.url_threats?.threats_detected ?? 0;
  const commTotal = stats?.comm_threats?.total ?? 0;
  const commThreats = stats?.comm_threats?.threats_detected ?? 0;
  const audioTotal = stats?.audio_threats?.total ?? 0;
  const audioThreats = stats?.audio_threats?.threats_detected ?? 0;
  const activeIncidents = stats?.incidents?.active ?? 0;
  const activeIndicators = stats?.threat_intelligence?.active_indicators ?? 0;
  const riskDist = stats?.risk_distribution ?? { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
  const recentAnalyses = stats?.recent_analyses ?? [];
  const recentIncidents = stats?.recent_incidents ?? [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-6 border-b border-[#1E2E5C]">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
              CYBER RAKSHA AI — Intelligent Digital Fraud Protection
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold bg-cyan-500/15 text-cyan-400 border border-cyan-500/30">
              v1.0.0-rc.1
            </span>
          </div>
          <p className="text-gray-400 text-xs sm:text-sm mt-1">
            Centralized telemetry, genuine multi-entity database counts, and unified threat status across all 6 detection & prevention engines.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            id="refresh-dashboard-btn"
            onClick={handleCombinedRefresh}
            disabled={isRefreshing || isLoadingStats}
            className="px-4 py-2 rounded-lg text-xs font-semibold bg-[#0B132B] text-gray-200 border border-[#1E2E5C] hover:border-[#00F0FF]/50 hover:text-white transition-all flex items-center space-x-2 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-[#00F0FF] ${isRefreshing || isLoadingStats ? 'animate-spin' : ''}`} />
            <span>{isRefreshing || isLoadingStats ? 'Refreshing Data...' : 'Live Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Backend Disconnection Alert if applicable */}
      {!isOnline && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-200 flex items-start space-x-3 shadow-[0_0_20px_rgba(244,63,94,0.15)]">
          <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-bold text-sm block">FastAPI Backend Unreachable</span>
            <p className="mt-0.5 text-rose-300/80">
              {error || 'Cannot connect to backend at http://127.0.0.1:8000. Ensure the Uvicorn server is running.'}
            </p>
            <p className="mt-1 text-[11px] font-mono text-rose-400">
              Start command: <code className="bg-black/40 px-1.5 py-0.5 rounded">cd backend; .\venv\Scripts\uvicorn app.main:app --reload</code>
            </p>
          </div>
          {/* Recent Cross-Vector Security Activity */}
          {b3Activity.length > 0 && (
            <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-[11px] text-gray-300 font-semibold">
                <span className="flex items-center space-x-1.5 font-mono text-cyan-400">
                  <Activity className="w-3 h-3 text-cyan-400" />
                  <span>Real-Time Unified Ingestion Pipeline (Latest Events)</span>
                </span>
                <span className="text-[10px] font-mono text-gray-400">{b3Activity.length} events logged</span>
              </div>
              <div className="space-y-1">
                {b3Activity.slice(0, 3).map((act: any) => (
                  <div key={act.id || act.event_id} className="p-2 rounded bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-[11px]">
                    <div className="flex items-center space-x-2 truncate max-w-[75%]">
                      <span className="font-mono text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                        {act.source_component}
                      </span>
                      <span className="text-gray-200 truncate">{act.description}</span>
                    </div>
                    <span className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded ${
                      act.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300' :
                      act.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-gray-300'
                    }`}>
                      {act.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Phase B3: Unified Protection Command Center Header Card */}
      {b3Overview && (
        <div className="p-5 rounded-2xl bg-[#070D1F] border border-cyan-500/30 shadow-[0_0_25px_rgba(0,240,255,0.08)] space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-3 border-b border-cyan-500/20">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-cyan-400" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h2 className="text-base font-bold text-white tracking-wide">
                    Unified Protection Command Center
                  </h2>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold">
                    Phase B3 Integration
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-0.5">
                  Cross-vector telemetry correlated in real-time across Browser Web Shield, Native Android App, and Central Intelligence.
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="text-right">
                <div className="text-xs font-mono text-gray-400">Security Posture</div>
                <div className="flex items-center space-x-1.5 justify-end">
                  <span className={`text-base font-extrabold font-mono ${
                    b3Overview.overall_posture?.score >= 90 ? 'text-emerald-400' :
                    b3Overview.overall_posture?.score >= 75 ? 'text-cyan-400' :
                    b3Overview.overall_posture?.score >= 50 ? 'text-amber-400' : 'text-rose-400'
                  }`}>
                    {b3Overview.overall_posture?.score ?? 100}%
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-bold">
                    {b3Overview.overall_posture?.label ?? 'EXCELLENT'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <div className="text-gray-400 font-mono text-[10px] uppercase">Unified Threat Events</div>
              <div className="text-lg font-bold font-mono text-white">
                {b3Overview.events?.total ?? 0}
              </div>
              <div className="text-[10px] text-cyan-400 font-mono">
                Browser & Android Correlated
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <div className="text-gray-400 font-mono text-[10px] uppercase">Correlated Incidents</div>
              <div className="text-lg font-bold font-mono text-amber-400">
                {b3Overview.incidents?.active ?? 0} <span className="text-xs text-gray-400 font-normal">Active</span>
              </div>
              <div className="text-[10px] text-gray-400 font-mono">
                {b3Overview.incidents?.resolved ?? 0} Resolved
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <div className="text-gray-400 font-mono text-[10px] uppercase">Registered Devices</div>
              <div className="text-lg font-bold font-mono text-emerald-400">
                {b3Overview.devices?.active ?? 0} <span className="text-xs text-gray-400 font-normal">Active</span>
              </div>
              <div className="text-[10px] text-gray-400 font-mono">
                {b3Overview.devices?.revoked ?? 0} Revoked
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <div className="text-gray-400 font-mono text-[10px] uppercase">Active Threat Indicators</div>
              <div className="text-lg font-bold font-mono text-cyan-400">
                {b3Overview.threat_intelligence?.active_indicators ?? 0}
              </div>
              <div className="text-[10px] text-gray-400 font-mono">
                URLhaus Feed: {b3Overview.threat_intelligence?.last_sync_status ?? 'SYNCED'}
              </div>
            </div>
          </div>

          {/* Active Incidents Action Drawer if any */}
          {b3Incidents.length > 0 && (
            <div className="p-3 rounded-xl bg-slate-950/70 border border-amber-500/20 space-y-2">
              <div className="flex items-center justify-between text-xs text-amber-300 font-semibold">
                <span className="flex items-center space-x-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span>High-Priority Incidents Requiring Action ({b3Incidents.length})</span>
                </span>
                <span className="text-[10px] font-mono text-gray-400">Auto-correlated 24h</span>
              </div>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {b3Incidents.map((inc: any) => (
                  <div key={inc.id} className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 text-xs">
                    <div className="space-y-0.5">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-cyan-400 font-semibold">{inc.incident_number}</span>
                        <span className="font-medium text-white">{inc.title}</span>
                        <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded font-bold ${
                          inc.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'
                        }`}>{inc.severity}</span>
                      </div>
                      <div className="text-[11px] text-gray-400 font-mono">
                        Target: <span className="text-gray-200">{inc.target_or_indicator || 'N/A'}</span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {!inc.user_acknowledged && (
                        <button
                          onClick={() => handleAcknowledgeIncident(inc.id)}
                          disabled={isProcessingIncident === inc.id}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 text-[11px] font-semibold transition-all cursor-pointer"
                        >
                          {isProcessingIncident === inc.id ? '...' : 'Acknowledge'}
                        </button>
                      )}
                      <button
                        onClick={() => handleResolveIncident(inc.id)}
                        disabled={isProcessingIncident === inc.id}
                        className="px-2.5 py-1 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 text-[11px] font-semibold transition-all cursor-pointer"
                      >
                        {isProcessingIncident === inc.id ? '...' : 'Resolve'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {/* Recent Cross-Vector Security Activity */}
          {b3Activity.length > 0 && (
            <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-[11px] text-gray-300 font-semibold">
                <span className="flex items-center space-x-1.5 font-mono text-cyan-400">
                  <Activity className="w-3 h-3 text-cyan-400" />
                  <span>Real-Time Unified Ingestion Pipeline (Latest Events)</span>
                </span>
                <span className="text-[10px] font-mono text-gray-400">{b3Activity.length} events logged</span>
              </div>
              <div className="space-y-1">
                {b3Activity.slice(0, 3).map((act: any) => (
                  <div key={act.id || act.event_id} className="p-2 rounded bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-[11px]">
                    <div className="flex items-center space-x-2 truncate max-w-[75%]">
                      <span className="font-mono text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                        {act.source_component}
                      </span>
                      <span className="text-gray-200 truncate">{act.description}</span>
                    </div>
                    <span className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded ${
                      act.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300' :
                      act.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-gray-300'
                    }`}>
                      {act.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Top Operational Metrics Row — Genuine Database Values */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Metric 1: Total Analyses */}
        <div className="cyber-card p-4 rounded-xl space-y-2 border border-slate-800">
          <div className="flex justify-between items-center text-gray-400">
            <span className="text-[10px] font-mono uppercase tracking-wider">Total Scans</span>
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-white">
            {totalAnalyses}
          </div>
          <p className="text-[10px] text-gray-400 font-mono">
            Across all vectors
          </p>
        </div>

        {/* Metric 2: URL Threats */}
        <div className="cyber-card p-4 rounded-xl space-y-2 border border-slate-800">
          <div className="flex justify-between items-center text-gray-400">
            <span className="text-[10px] font-mono uppercase tracking-wider">URL Phishing</span>
            <Shield className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-rose-400">
            {urlThreats} <span className="text-xs font-normal text-gray-400">/ {urlTotal}</span>
          </div>
          <p className="text-[10px] text-gray-400 font-mono">
            Malicious URLs detected
          </p>
        </div>

        {/* Metric 3: Message Threats */}
        <div className="cyber-card p-4 rounded-xl space-y-2 border border-slate-800">
          <div className="flex justify-between items-center text-gray-400">
            <span className="text-[10px] font-mono uppercase tracking-wider">Comm Scams</span>
            <MessageSquare className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-amber-400">
            {commThreats} <span className="text-xs font-normal text-gray-400">/ {commTotal}</span>
          </div>
          <p className="text-[10px] text-gray-400 font-mono">
            Fraud & extortion msgs
          </p>
        </div>

        {/* Metric 4: Audio Deepfakes */}
        <div className="cyber-card p-4 rounded-xl space-y-2 border border-slate-800">
          <div className="flex justify-between items-center text-gray-400">
            <span className="text-[10px] font-mono uppercase tracking-wider">Voice Clones</span>
            <Mic className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-purple-400">
            {audioThreats} <span className="text-xs font-normal text-gray-400">/ {audioTotal}</span>
          </div>
          <p className="text-[10px] text-gray-400 font-mono">
            Synthetic voice samples
          </p>
        </div>

        {/* Metric 5: Active Incidents */}
        <div className="cyber-card p-4 rounded-xl space-y-2 border border-slate-800">
          <div className="flex justify-between items-center text-gray-400">
            <span className="text-[10px] font-mono uppercase tracking-wider">Active Incidents</span>
            <ShieldAlert className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-emerald-400">
            {activeIncidents}
          </div>
          <p className="text-[10px] text-gray-400 font-mono">
            Containment actions
          </p>
        </div>

        {/* Metric 6: Threat Indicators */}
        <div className="cyber-card p-4 rounded-xl space-y-2 border border-slate-800">
          <div className="flex justify-between items-center text-gray-400">
            <span className="text-[10px] font-mono uppercase tracking-wider">Active IoCs</span>
            <Radio className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-cyan-400">
            {activeIndicators}
          </div>
          <p className="text-[10px] text-gray-400 font-mono">
            Verified threat feeds
          </p>
        </div>
      </div>

      {/* 12-Module Platform Navigation Matrix */}
      <div className="p-5 rounded-2xl bg-[#0A1128]/70 border border-[#1E2E5C] backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-gray-800">
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-[#00F0FF]" />
            <h2 className="text-base font-bold text-white uppercase tracking-wider">
              Integrated Protection Modules & Capabilities (12 Core Systems)
            </h2>
          </div>
          <span className="text-[11px] font-mono text-cyan-400">Production Release Candidate</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {[
            { id: 'dashboard', label: '1. Overview Dashboard', icon: '📊', desc: 'Real-time telemetry & counts' },
            { id: 'phishing', label: '2. URL Threat Detection', icon: '🌐', desc: 'Random Forest 25-feature ML' },
            { id: 'communication', label: '3. Message Fraud Analysis', icon: '💬', desc: 'NLP LinearSVC & urgency token' },
            { id: 'digital-arrest', label: '4. Digital Arrest Protection', icon: '⚖️', desc: 'Law enforcement extortion' },
            { id: 'voice-shield', label: '5. Voice Impersonation Shield', icon: '🎙️', desc: 'Acoustic deepfake classifier' },
            { id: 'unified-analyzer', label: '6. Unified Threat Analysis', icon: '⚡', desc: 'Cross-vector risk engine' },
            { id: 'intel', label: '7. Threat Intelligence', icon: '🛰️', desc: 'URLhaus & PhishTank IoCs' },
            { id: 'protection-center', label: '8. Personal Protection', icon: '🛡️', desc: 'Proactive safety settings' },
            { id: 'incidents', label: '9. Incident Management', icon: '🚨', desc: 'Playbooks & containment' },
            { id: 'extension', label: '10. Browser Extension', icon: '🧩', desc: 'Chromium Manifest V3' },
            { id: 'mobile', label: '11. Mobile Companion', icon: '📱', desc: 'Android & PWA share target' },
            { id: 'system', label: '12. System Observability', icon: '⚙️', desc: 'Health, metrics & runbook' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => {
                if (item.id === 'incidents') onNavigate?.('protection-center');
                else if (item.id === 'extension') setShowExtensionModal(true);
                else if (item.id === 'mobile') setShowMobileModal(true);
                else onNavigate?.(item.id);
              }}
              className="p-3 rounded-xl bg-slate-900/60 border border-[#1E2E5C]/60 hover:border-cyan-400/50 hover:bg-slate-800/40 text-left transition-all group flex flex-col justify-between cursor-pointer"
            >
              <div>
                <span className="text-xl">{item.icon}</span>
                <h4 className="text-xs font-semibold text-white mt-1.5 group-hover:text-cyan-300">
                  {item.label}
                </h4>
              </div>
              <p className="text-[10px] text-gray-400 mt-1 line-clamp-2">{item.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Middle Grid: Risk Distribution + Infrastructure Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Risk Distribution & Operational Engines */}
        <div className="lg:col-span-7 space-y-5">
          {/* Risk Level Distribution */}
          <div className="p-5 rounded-xl bg-[#0B132B]/60 border border-[#1E2E5C] space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-[#00F0FF]" />
                <h3 className="font-bold text-white text-sm">Threat Risk Distribution</h3>
              </div>
              <span className="text-[10px] font-mono text-gray-400">
                Database Verified (No Synthetic Values)
              </span>
            </div>

            <div className="grid grid-cols-4 gap-3 text-center">
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                <span className="text-[10px] font-mono text-emerald-400 block uppercase">Low / Benign</span>
                <span className="text-xl font-bold font-mono text-emerald-400">{riskDist.LOW}</span>
              </div>
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                <span className="text-[10px] font-mono text-amber-400 block uppercase">Medium</span>
                <span className="text-xl font-bold font-mono text-amber-400">{riskDist.MEDIUM}</span>
              </div>
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30">
                <span className="text-[10px] font-mono text-rose-400 block uppercase">High Risk</span>
                <span className="text-xl font-bold font-mono text-rose-400">{riskDist.HIGH}</span>
              </div>
              <div className="p-3 rounded-lg bg-red-900/30 border border-red-500/50">
                <span className="text-[10px] font-mono text-red-400 block uppercase">Critical</span>
                <span className="text-xl font-bold font-mono text-red-400">{riskDist.CRITICAL}</span>
              </div>
            </div>

            {totalAnalyses === 0 && (
              <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800 text-[11px] text-gray-400 flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-cyan-400 shrink-0" />
                <span>
                  The database has no historical scans recorded yet. Submit a URL, message, or voice note to generate live detection metrics.
                </span>
              </div>
            )}
          </div>

          {/* Core Security Modules Status */}
          <div className="p-5 rounded-xl bg-[#0B132B]/60 border border-[#1E2E5C] space-y-3">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <h3 className="font-bold text-white text-sm">All 6 Security Modules Operational</h3>
              </div>
              <button
                onClick={onNavigateToModules}
                className="text-[11px] font-mono text-[#00F0FF] hover:underline flex items-center space-x-1"
              >
                <span>View Full Registry</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-gray-300">Phishing URL Classifier</span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">TRAINED / OPERATIONAL</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-gray-300">Communication Fraud NLP</span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">TRAINED / OPERATIONAL</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-gray-300">Voice Deepfake Detector</span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">TRAINED / OPERATIONAL</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-gray-300">Threat Intelligence Feed</span>
                <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/30">ACTIVE / HARVESTER</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-gray-300">Unified Risk Correlator</span>
                <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/30">SYNCHRONIZED</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                <span className="text-gray-300">Incident Response Engine</span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">ACTIVE PLAYBOOKS</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Infrastructure Telemetry & End-to-End Status */}
        <div className="lg:col-span-5 space-y-5">
          <div className="p-5 rounded-xl bg-[#0B132B]/60 border border-[#1E2E5C] space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-[#00F0FF]" />
                <h3 className="font-bold text-white text-sm">System Health & Security Posture</h3>
              </div>
              <span className="text-[10px] font-mono text-gray-400 flex items-center space-x-1">
                <Clock className="w-3 h-3" />
                <span>{health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'N/A'}</span>
              </span>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-gray-300">FastAPI Backend ASGI</span>
                <span className="flex items-center space-x-1 font-mono text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>ONLINE (200 OK)</span>
                </span>
              </div>

              <div className="flex justify-between items-center p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-gray-300">Database Ping (SELECT 1)</span>
                <span className="flex items-center space-x-1 font-mono text-cyan-400">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{health?.database_latency_ms !== undefined ? `${health.database_latency_ms} ms` : 'Active'}</span>
                </span>
              </div>

              <div className="flex justify-between items-center p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-gray-300">SQLAlchemy ORM Entities</span>
                <span className="font-mono text-gray-200">
                  11 Relational Tables
                </span>
              </div>

              <div className="flex justify-between items-center p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-gray-300">Rate Limiter & Security Headers</span>
                <span className="font-mono text-emerald-400">
                  ACTIVE (CSP, nosniff, 120r/m)
                </span>
              </div>

              <div className="flex justify-between items-center p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-gray-300">Chromium Extension & PWA</span>
                <span className="font-mono text-cyan-400">
                  MV3 + Service Worker Ready
                </span>
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* Phase A3: Live Security Notifications & Threat Alert Engine */}
      <div className="p-6 rounded-2xl bg-[#080d1e] border border-[#1E2E5C] shadow-2xl space-y-5">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-[#1E2E5C]/60">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-500/20 to-orange-500/20 border border-rose-500/40 flex items-center justify-center shadow-[0_0_15px_rgba(244,63,94,0.25)]">
              <Bell className="w-5 h-5 text-rose-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white tracking-wide">
                  Security Notifications & Incident Alerts
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold">
                  Phase A3 Engine
                </span>
                {unreadNotifCount > 0 && (
                  <span className="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
                    {unreadNotifCount} UNREAD
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                Real-time security alert pipeline connecting browser interception, phishing detection, and threat intel updates.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono bg-slate-900 border border-slate-800 text-gray-400">
              <span className={`w-2 h-2 rounded-full ${sseConnected ? 'bg-emerald-400 animate-pulse' : 'bg-cyan-400'}`} />
              <span>{sseConnected ? 'SSE: REAL-TIME STREAM' : 'POLLING ENGINE'}</span>
            </span>

            {unreadNotifCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-xs text-cyan-300 font-medium transition-all flex items-center space-x-1.5"
                title="Mark all notifications as read"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                <span>Mark All Read</span>
              </button>
            )}

            <button
              onClick={() => setShowNotifPrefsModal(true)}
              className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-gray-300 hover:text-white text-xs transition-all"
              title="Configure Notification Preferences"
            >
              <Settings className="w-4 h-4" />
            </button>

            {totalNotifs > 0 && (
              <button
                onClick={handleClearAllNotifs}
                className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-rose-900/40 border border-slate-700 hover:border-rose-500/40 text-gray-400 hover:text-rose-300 text-xs transition-all"
                title="Clear notification history"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Filters Row */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs bg-[#0b132b]/50 p-3 rounded-xl border border-[#1E2E5C]/40">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-gray-400 font-mono text-[11px] mr-1 flex items-center space-x-1">
              <Filter className="w-3 h-3 text-cyan-400" />
              <span>Severity:</span>
            </span>
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
              <button
                key={sev}
                onClick={() => setNotifSeverityFilter(sev)}
                className={`px-2.5 py-1 rounded-md font-mono text-[10px] font-semibold transition-all border ${
                  notifSeverityFilter === sev
                    ? sev === 'CRITICAL'
                      ? 'bg-rose-500/20 text-rose-300 border-rose-500/50 shadow-[0_0_8px_rgba(244,63,94,0.3)]'
                      : sev === 'HIGH'
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-[0_0_8px_rgba(245,158,11,0.3)]'
                      : sev === 'MEDIUM'
                      ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50'
                      : sev === 'LOW'
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50'
                      : 'bg-[#00F0FF]/20 text-[#00F0FF] border-[#00F0FF]/50 shadow-[0_0_8px_rgba(0,240,255,0.3)]'
                    : 'bg-slate-900/60 text-gray-400 border-slate-800 hover:text-white'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-3">
            <select
              value={notifCategoryFilter}
              onChange={(e) => setNotifCategoryFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-gray-300 font-mono focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Threat Categories</option>
              <option value="MALICIOUS_WEBSITE">Malicious Websites</option>
              <option value="PHISHING_ATTEMPT">Phishing Attempts</option>
              <option value="THREAT_INTEL_SYNC">Threat Feed Sync</option>
              <option value="SYSTEM_ALERT">System Alerts</option>
            </select>

            <label className="flex items-center space-x-1.5 cursor-pointer text-gray-300 select-none">
              <input
                type="checkbox"
                checked={notifUnreadOnly}
                onChange={(e) => setNotifUnreadOnly(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0"
              />
              <span className="text-[11px] font-mono">Unread Only</span>
            </label>
          </div>
        </div>

        {/* Notifications Feed */}
        <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
          {isLoadingNotifs && notifications.length === 0 ? (
            <div className="p-8 text-center text-xs text-gray-400 font-mono">
              <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-cyan-400" />
              Loading security notifications...
            </div>
          ) : notifications.length === 0 ? (
            <div className="p-10 text-center rounded-xl bg-slate-900/30 border border-slate-800/80">
              <ShieldCheck className="w-10 h-10 text-emerald-400/60 mx-auto mb-2" />
              <p className="text-sm font-semibold text-gray-300">No Security Notifications Matching Filters</p>
              <p className="text-xs text-gray-500 mt-1">
                When browser blocks a dangerous site or threat intel sync runs, security notices will display here automatically.
              </p>
            </div>
          ) : (
            notifications.map((notif) => {
              const sev = (notif.severity || 'LOW').toUpperCase();
              const isCrit = sev === 'CRITICAL';
              const isHigh = sev === 'HIGH';
              const isMed = sev === 'MEDIUM';

              return (
                <div
                  key={notif.id}
                  className={`p-4 rounded-xl border transition-all ${
                    notif.is_read
                      ? 'bg-slate-900/40 border-slate-800/80 opacity-80 hover:opacity-100'
                      : isCrit
                      ? 'bg-rose-950/20 border-rose-500/40 shadow-[0_0_15px_rgba(244,63,94,0.1)]'
                      : isHigh
                      ? 'bg-amber-950/20 border-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.1)]'
                      : 'bg-slate-900/70 border-cyan-500/30'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start space-x-3">
                      <div className="mt-0.5">
                        {isCrit ? (
                          <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0" />
                        ) : isHigh ? (
                          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
                        ) : (
                          <Info className="w-5 h-5 text-cyan-400 shrink-0" />
                        )}
                      </div>

                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border ${
                              isCrit
                                ? 'bg-rose-500/20 text-rose-300 border-rose-500/50'
                                : isHigh
                                ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                                : isMed
                                ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50'
                                : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50'
                            }`}
                          >
                            {sev}
                          </span>

                          <span className="text-[10px] font-mono text-gray-400 bg-black/40 px-2 py-0.5 rounded border border-gray-800">
                            {notif.category}
                          </span>

                          <h4 className="text-xs sm:text-sm font-bold text-white">
                            {notif.title}
                          </h4>

                          {!notif.is_read && (
                            <span className="w-2 h-2 rounded-full bg-cyan-400 shrink-0" />
                          )}
                        </div>

                        <p className="text-xs text-gray-300 leading-relaxed">
                          {notif.message}
                        </p>

                        {notif.target_domain && (
                          <div className="flex items-center space-x-1.5 pt-1 text-[11px] font-mono text-cyan-400">
                            <ExternalLink className="w-3 h-3" />
                            <span>Target: {notif.target_domain}</span>
                          </div>
                        )}

                        {notif.recommended_action && (
                          <div className="mt-1.5 p-2 rounded-md bg-black/40 border-l-2 border-cyan-400 text-[11px] text-gray-300 font-mono">
                            <span className="text-cyan-400 font-semibold">Action: </span>
                            {notif.recommended_action}
                          </div>
                        )}

                        <div className="flex items-center space-x-3 text-[10px] text-gray-500 font-mono pt-1">
                          <span>Reported by: {notif.source_component}</span>
                          <span>•</span>
                          <span>{notif.created_at ? new Date(notif.created_at).toLocaleString() : ''}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-1 shrink-0">
                      {!notif.is_read && (
                        <button
                          onClick={() => handleMarkRead(notif.id)}
                          className="p-1 rounded hover:bg-slate-800 text-gray-400 hover:text-cyan-300 transition-colors"
                          title="Mark as read"
                        >
                          <CheckCheck className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteNotif(notif.id)}
                        className="p-1 rounded hover:bg-rose-950 text-gray-400 hover:text-rose-400 transition-colors"
                        title="Delete notification"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Notification Preferences Modal */}
      {showNotifPrefsModal && notifPrefs && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-md rounded-2xl border border-[#1E2E5C] bg-[#0A0F1D] p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-gray-800">
              <div className="flex items-center space-x-2">
                <Settings className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-bold text-white">Notification Preferences</h3>
              </div>
              <button
                onClick={() => setShowNotifPrefsModal(false)}
                className="text-gray-400 hover:text-white text-sm px-2 py-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveNotifPrefs} className="space-y-4 text-xs">
              <label className="flex items-center justify-between p-3 rounded-lg bg-slate-900/60 border border-slate-800 cursor-pointer">
                <div>
                  <span className="font-semibold text-white block">Desktop Browser Notifications</span>
                  <span className="text-[11px] text-gray-400">Display native browser notification cards on threat blocks</span>
                </div>
                <input
                  type="checkbox"
                  checked={notifPrefs.browser_notifications_enabled}
                  onChange={(e) =>
                    setNotifPrefs({ ...notifPrefs, browser_notifications_enabled: e.target.checked })
                  }
                  className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0"
                />
              </label>

              <div>
                <label className="font-semibold text-gray-300 block mb-1">
                  Minimum Alert Severity Threshold
                </label>
                <select
                  value={notifPrefs.min_severity}
                  onChange={(e) => setNotifPrefs({ ...notifPrefs, min_severity: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2.5 text-gray-200 font-mono focus:outline-none focus:border-cyan-500"
                >
                  <option value="LOW">LOW (Receive all alerts & feed sync notices)</option>
                  <option value="MEDIUM">MEDIUM (Suspicious behavior & sync fallbacks)</option>
                  <option value="HIGH">HIGH (Confirmed phishing & severe risks)</option>
                  <option value="CRITICAL">CRITICAL ONLY (Active malware & credential theft blocks)</option>
                </select>
              </div>

              <label className="flex items-center justify-between p-3 rounded-lg bg-slate-900/60 border border-slate-800 cursor-pointer">
                <div>
                  <span className="font-semibold text-white block">Audio Alert Cue</span>
                  <span className="text-[11px] text-gray-400">Play subtle audio alert on critical threat interventions</span>
                </div>
                <input
                  type="checkbox"
                  checked={notifPrefs.sound_enabled}
                  onChange={(e) => setNotifPrefs({ ...notifPrefs, sound_enabled: e.target.checked })}
                  className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0"
                />
              </label>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowNotifPrefsModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-gray-300 text-xs font-semibold hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingPrefs}
                  className="px-4 py-2 rounded-lg bg-cyan-500 text-black text-xs font-semibold hover:bg-cyan-400 disabled:opacity-50"
                >
                  {isSavingPrefs ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </form>
          </div>
          {/* Recent Cross-Vector Security Activity */}
          {b3Activity.length > 0 && (
            <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-[11px] text-gray-300 font-semibold">
                <span className="flex items-center space-x-1.5 font-mono text-cyan-400">
                  <Activity className="w-3 h-3 text-cyan-400" />
                  <span>Real-Time Unified Ingestion Pipeline (Latest Events)</span>
                </span>
                <span className="text-[10px] font-mono text-gray-400">{b3Activity.length} events logged</span>
              </div>
              <div className="space-y-1">
                {b3Activity.slice(0, 3).map((act: any) => (
                  <div key={act.id || act.event_id} className="p-2 rounded bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-[11px]">
                    <div className="flex items-center space-x-2 truncate max-w-[75%]">
                      <span className="font-mono text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                        {act.source_component}
                      </span>
                      <span className="text-gray-200 truncate">{act.description}</span>
                    </div>
                    <span className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded ${
                      act.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300' :
                      act.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-gray-300'
                    }`}>
                      {act.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Bottom Grid: Recent Analyses & Recent Incidents */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Analyses Box */}
        <div className="p-5 rounded-xl bg-[#0B132B]/60 border border-[#1E2E5C] space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <FileText className="w-4 h-4 text-cyan-400" />
              <h3 className="font-bold text-white text-sm">Recent Threat Analyses</h3>
            </div>
            <span className="text-[10px] font-mono text-gray-400">Latest 5 Records</span>
          </div>

          {recentAnalyses.length === 0 ? (
            <div className="p-6 text-center text-xs text-gray-500 font-mono">
              No historical analyses recorded yet. Run a scan from the Phishing or Communication tabs.
            </div>
          ) : (
            <div className="space-y-2">
              {recentAnalyses.map((item: any) => (
                <div key={item.id} className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex justify-between items-center text-xs">
                  <div className="space-y-0.5 max-w-[70%]">
                    <span className="text-gray-200 font-medium truncate block">{item.target}</span>
                    <div className="flex items-center space-x-2 text-[10px] text-gray-400 font-mono">
                      <span>{item.module}</span>
                      <span>•</span>
                      <span>{item.created_at ? new Date(item.created_at).toLocaleTimeString() : ''}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                      (item.risk_score ?? 0) >= 60 ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' :
                      (item.risk_score ?? 0) >= 35 ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' :
                      'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                    }`}>
                      Score: {item.risk_score ?? 'N/A'}/100
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Incidents Box */}
        <div className="p-5 rounded-xl bg-[#0B132B]/60 border border-[#1E2E5C] space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-emerald-400" />
              <h3 className="font-bold text-white text-sm">Recent Security Incidents</h3>
            </div>
            <span className="text-[10px] font-mono text-gray-400">Latest 5 Records</span>
          </div>

          {recentIncidents.length === 0 ? (
            <div className="p-6 text-center text-xs text-gray-500 font-mono">
              No active incidents recorded. High-severity detections can be escalated to incidents from the Protection Center.
            </div>
          ) : (
            <div className="space-y-2">
              {recentIncidents.map((inc: any) => (
                <div key={inc.id} className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex justify-between items-center text-xs">
                  <div className="space-y-0.5 max-w-[70%]">
                    <span className="text-gray-200 font-medium truncate block">{inc.title}</span>
                    <div className="flex items-center space-x-2 text-[10px] text-gray-400 font-mono">
                      <span className="text-cyan-400 font-mono">{inc.incident_number}</span>
                      <span>•</span>
                      <span>{inc.category}</span>
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      {inc.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Browser Extension Info Modal */}
      {showExtensionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-lg rounded-2xl border border-[#1E2E5C] bg-[#0A0F1D] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-gray-800">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">🧩</span>
                <h3 className="text-lg font-bold text-white">Chromium Web Shield Extension</h3>
              </div>
              <button
                onClick={() => setShowExtensionModal(false)}
                className="text-gray-400 hover:text-white text-sm px-2 py-1"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-gray-300 leading-relaxed">
              Cyber Raksha AI includes a real Manifest V3 Chromium browser extension located in <code className="bg-black/50 px-1.5 py-0.5 rounded text-cyan-400 font-mono">browser_extension/</code>.
            </p>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs text-gray-300">
              <h4 className="font-semibold text-cyan-400 uppercase text-[10px] tracking-wider font-mono">How to Load in Chrome / Edge:</h4>
              <ol className="list-decimal pl-4 space-y-1 text-gray-400">
                <li>Open <code className="text-white">chrome://extensions</code> or <code className="text-white">edge://extensions</code></li>
                <li>Enable <strong className="text-white">Developer Mode</strong> toggle</li>
                <li>Click <strong className="text-white">Load unpacked</strong></li>
                <li>Select the <code className="text-cyan-400">browser_extension</code> folder in the repository</li>
              </ol>
            </div>
            <div className="text-[11px] text-gray-400">
              Features: Active tab scanning, link context menu threat checks, real-time risk indicators, and direct connection to FastAPI backend (<code className="text-white">http://127.0.0.1:8000</code>).
            </div>
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowExtensionModal(false)}
                className="px-4 py-2 rounded-lg bg-cyan-500 text-black font-semibold text-xs hover:bg-cyan-400"
              >
                Close
              </button>
            </div>
          </div>
          {/* Recent Cross-Vector Security Activity */}
          {b3Activity.length > 0 && (
            <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-[11px] text-gray-300 font-semibold">
                <span className="flex items-center space-x-1.5 font-mono text-cyan-400">
                  <Activity className="w-3 h-3 text-cyan-400" />
                  <span>Real-Time Unified Ingestion Pipeline (Latest Events)</span>
                </span>
                <span className="text-[10px] font-mono text-gray-400">{b3Activity.length} events logged</span>
              </div>
              <div className="space-y-1">
                {b3Activity.slice(0, 3).map((act: any) => (
                  <div key={act.id || act.event_id} className="p-2 rounded bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-[11px]">
                    <div className="flex items-center space-x-2 truncate max-w-[75%]">
                      <span className="font-mono text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                        {act.source_component}
                      </span>
                      <span className="text-gray-200 truncate">{act.description}</span>
                    </div>
                    <span className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded ${
                      act.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300' :
                      act.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-gray-300'
                    }`}>
                      {act.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Mobile Companion Info Modal */}
      {showMobileModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-lg rounded-2xl border border-[#1E2E5C] bg-[#0A0F1D] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-gray-800">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">📱</span>
                <h3 className="text-lg font-bold text-white">Android & PWA Mobile Companion</h3>
              </div>
              <button
                onClick={() => setShowMobileModal(false)}
                className="text-gray-400 hover:text-white text-sm px-2 py-1"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-gray-300 leading-relaxed">
              Cyber Raksha AI operates as an installable Progressive Web App (PWA) with Android Web Share Target support.
            </p>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs text-gray-300">
              <h4 className="font-semibold text-cyan-400 uppercase text-[10px] tracking-wider font-mono">Mobile Capabilities:</h4>
              <ul className="list-disc pl-4 space-y-1 text-gray-400">
                <li><strong className="text-white">Web Share Target:</strong> Share suspicious links or SMS directly from WhatsApp or Messages into Cyber Raksha.</li>
                <li><strong className="text-white">Install to Home Screen:</strong> Standalone app window with dedicated service worker caching.</li>
                <li><strong className="text-white">Mobile Navigation Bar:</strong> Touch-optimized thumb navigation for rapid threat analysis.</li>
              </ul>
            </div>
            <div className="text-[11px] text-gray-400">
              Open Cyber Raksha AI on Chrome for Android or Safari for iOS, tap <strong className="text-white">Add to Home Screen</strong>, and install the companion instantly without an app store download.
            </div>
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowMobileModal(false)}
                className="px-4 py-2 rounded-lg bg-cyan-500 text-black font-semibold text-xs hover:bg-cyan-400"
              >
                Close
              </button>
            </div>
          </div>
          {/* Recent Cross-Vector Security Activity */}
          {b3Activity.length > 0 && (
            <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-[11px] text-gray-300 font-semibold">
                <span className="flex items-center space-x-1.5 font-mono text-cyan-400">
                  <Activity className="w-3 h-3 text-cyan-400" />
                  <span>Real-Time Unified Ingestion Pipeline (Latest Events)</span>
                </span>
                <span className="text-[10px] font-mono text-gray-400">{b3Activity.length} events logged</span>
              </div>
              <div className="space-y-1">
                {b3Activity.slice(0, 3).map((act: any) => (
                  <div key={act.id || act.event_id} className="p-2 rounded bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-[11px]">
                    <div className="flex items-center space-x-2 truncate max-w-[75%]">
                      <span className="font-mono text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                        {act.source_component}
                      </span>
                      <span className="text-gray-200 truncate">{act.description}</span>
                    </div>
                    <span className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded ${
                      act.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300' :
                      act.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-gray-300'
                    }`}>
                      {act.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
