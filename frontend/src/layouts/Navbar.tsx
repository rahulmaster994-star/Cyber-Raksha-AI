import React, { useState, useEffect, useRef } from 'react';
import { Shield, Activity, Database, Server, Cpu, Layers, Bell, CheckCheck, AlertTriangle, ShieldAlert, Info } from 'lucide-react';
import { apiService } from '../services/api';
import type { HealthCheckData, NotificationItem } from '../services/api';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  health: HealthCheckData | null;
  isOnline: boolean;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  health,
  isOnline,
  onRefresh,
  isRefreshing,
}) => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchNotifs = async () => {
    try {
      const res = await apiService.getNotifications({ limit: 5 });
      if (res.data) {
        setNotifications(res.data.items);
        setUnreadCount(res.data.unread_count);
      }
    } catch (_) {}
  };

  useEffect(() => {
    fetchNotifs();

    // Subscribe to real-time SSE stream
    const unsubscribe = apiService.subscribeNotificationStream((newItem) => {
      setNotifications((prev) => [newItem, ...prev.slice(0, 4)]);
      setUnreadCount((prev) => prev + 1);
    });

    // Fallback polling interval every 12 seconds
    const interval = setInterval(fetchNotifs, 12000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkAllRead = async () => {
    await apiService.markAllNotificationsRead();
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
  };

  const handleMarkRead = async (id: number) => {
    await apiService.markNotificationRead(id);
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    setUnreadCount((prev) => Math.max(0, prev - 1));
  };
  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-md bg-[#050811]/85 border-b border-[#1E2E5C]/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Stage 1 Badge */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentTab('landing')}>
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#00F0FF]/20 to-[#0070F3]/30 border border-[#00F0FF]/40 flex items-center justify-center shadow-[0_0_15px_rgba(0,240,255,0.25)]">
              <Shield className="w-5 h-5 text-[#00F0FF]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-bold tracking-wider text-white cyber-glow-text">
                  CYBER RAKSHA
                </span>
                <span className="text-xs px-1.5 py-0.5 rounded bg-[#00F0FF]/15 text-[#00F0FF] border border-[#00F0FF]/30 font-mono font-semibold">
                  AI
                </span>
              </div>
              <span className="text-[10px] text-cyan-400 font-mono tracking-widest uppercase block">
                Stage 10: Release Candidate (v1.0.0-rc.1)
              </span>
            </div>
          </div>

          {/* Nav Links */}
          <nav className="hidden md:flex items-center space-x-1">
            <button
              id="nav-landing"
              onClick={() => setCurrentTab('landing')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                currentTab === 'landing'
                  ? 'bg-[#00F0FF]/15 text-[#00F0FF] border border-[#00F0FF]/30 shadow-[0_0_10px_rgba(0,240,255,0.2)]'
                  : 'text-gray-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              Overview
            </button>
            <button
              id="nav-dashboard"
              onClick={() => setCurrentTab('dashboard')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                currentTab === 'dashboard'
                  ? 'bg-[#00F0FF]/15 text-[#00F0FF] border border-[#00F0FF]/30 shadow-[0_0_10px_rgba(0,240,255,0.2)]'
                  : 'text-gray-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>Control Center</span>
            </button>
            <button
              id="nav-phishing"
              onClick={() => setCurrentTab('phishing')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                currentTab === 'phishing'
                  ? 'bg-[#00F0FF]/15 text-[#00F0FF] border border-[#00F0FF]/30 shadow-[0_0_10px_rgba(0,240,255,0.2)]'
                  : 'text-gray-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <Shield className="w-4 h-4 text-[#00F0FF]" />
              <span>Phishing Detection</span>
            </button>
            <button
              id="nav-communication"
              onClick={() => setCurrentTab('communication')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                currentTab === 'communication'
                  ? 'bg-[#00F0FF]/15 text-[#00F0FF] border border-[#00F0FF]/30 shadow-[0_0_10px_rgba(0,240,255,0.2)]'
                  : 'text-gray-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <span>Message Threats</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-mono">
                Stage 3
              </span>
            </button>
            <button
              id="nav-digital-arrest"
              onClick={() => setCurrentTab('digital-arrest')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                currentTab === 'digital-arrest'
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-[0_0_10px_rgba(244,63,94,0.3)]'
                  : 'text-gray-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <span className="text-rose-400 font-bold">●</span>
              <span>Digital Arrest</span>
            </button>
            <button
              id="nav-voice-shield"
              onClick={() => setCurrentTab('voice-shield')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                currentTab === 'voice-shield'
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-[0_0_10px_rgba(168,85,247,0.3)]'
                  : 'text-gray-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <span>Voice Shield</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-mono">
                Stage 4
              </span>
            </button>
            <button
              id="nav-threat-intel"
              onClick={() => setCurrentTab('intel')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                currentTab === 'intel'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-[0_0_10px_rgba(245,158,11,0.3)]'
                  : 'text-gray-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <span>Threat Intel</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono">
                Stage 5
              </span>
            </button>
            <button
              id="nav-unified-analyzer"
              onClick={() => setCurrentTab('unified-analyzer')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                currentTab === 'unified-analyzer'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(0,240,255,0.3)]'
                  : 'text-gray-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <span>Unified Risk</span>
            </button>
            <button
              id="nav-protection-center"
              onClick={() => setCurrentTab('protection-center')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                currentTab === 'protection-center'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.3)]'
                  : 'text-gray-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <span>Protection Center</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono">
                Stage 6
              </span>
            </button>
            <button
              id="nav-modules"
              onClick={() => setCurrentTab('modules')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                currentTab === 'modules'
                  ? 'bg-[#00F0FF]/15 text-[#00F0FF] border border-[#00F0FF]/30 shadow-[0_0_10px_rgba(0,240,255,0.2)]'
                  : 'text-gray-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <Cpu className="w-4 h-4" />
              <span>Security Modules</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-yellow-500/20 text-yellow-300 border border-yellow-500/30">
                Planned
              </span>
            </button>
            <button
              id="nav-system"
              onClick={() => setCurrentTab('system')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                currentTab === 'system'
                  ? 'bg-[#00F0FF]/15 text-[#00F0FF] border border-[#00F0FF]/30 shadow-[0_0_10px_rgba(0,240,255,0.2)]'
                  : 'text-gray-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>System Info</span>
            </button>
            <button
              id="nav-admin"
              onClick={() => setCurrentTab('admin')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center space-x-1.5 ${
                currentTab === 'admin'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(0,240,255,0.3)]'
                  : 'text-gray-300 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <span>Admin</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-mono">
                Ops
              </span>
            </button>
          </nav>

          {/* Live Telemetry Status Pills */}
          <div className="flex items-center space-x-3">
            {/* Backend Pill */}
            <div
              className={`hidden sm:flex items-center space-x-2 px-2.5 py-1 rounded-full text-xs font-mono border ${
                isOnline
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
              }`}
              title="FastAPI Backend Connectivity"
            >
              <span
                className={`pulse-indicator ${
                  isOnline ? 'bg-emerald-400' : 'bg-rose-400'
                }`}
              />
              <Server className="w-3.5 h-3.5" />
              <span>{isOnline ? 'API: ONLINE' : 'API: OFFLINE'}</span>
              {isOnline && health?.database_latency_ms !== undefined && (
                <span className="text-[10px] text-gray-400">
                  ({health.database_latency_ms}ms)
                </span>
              )}
            </div>

            {/* DB Pill */}
            <div
              className={`hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono border ${
                health?.database_connected
                  ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                  : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
              }`}
              title="SQLAlchemy Database Connectivity"
            >
              <Database className="w-3.5 h-3.5" />
              <span>{health?.database_connected ? 'DB: ACTIVE' : 'DB: OFFLINE'}</span>
            </div>

            {/* Live Refresh Trigger */}
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className={`p-1.5 rounded-lg border border-[#1E2E5C] text-gray-300 hover:text-[#00F0FF] hover:border-[#00F0FF]/40 transition-all ${
                isRefreshing ? 'animate-spin text-[#00F0FF]' : ''
              }`}
              title="Refresh System Health"
            >
              <Activity className="w-4 h-4" />
            </button>

            {/* Phase A3: Security Alerts & Notification Dropdown */}
            <div className="relative" ref={dropdownRef}>
              <button
                id="btn-notification-bell"
                onClick={() => setIsOpen(!isOpen)}
                className={`p-1.5 rounded-lg border border-[#1E2E5C] text-gray-300 hover:text-[#00F0FF] hover:border-[#00F0FF]/40 transition-all relative ${
                  isOpen ? 'bg-[#00F0FF]/15 border-[#00F0FF]/40 text-[#00F0FF]' : ''
                }`}
                title="Security Notifications & Real-Time Alerts"
              >
                <Bell className="w-4 h-4" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow-lg animate-pulse">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {isOpen && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-xl bg-[#080d1e] border border-[#1E2E5C] shadow-[0_10px_35px_rgba(0,0,0,0.8)] z-50 overflow-hidden backdrop-blur-xl">
                  {/* Dropdown Header */}
                  <div className="flex items-center justify-between px-4 py-3 border-b border-[#1E2E5C]/60 bg-[#0d142d]">
                    <div className="flex items-center space-x-2">
                      <ShieldAlert className="w-4 h-4 text-[#00F0FF]" />
                      <span className="text-xs font-bold text-white uppercase tracking-wider">
                        Security Alerts
                      </span>
                      {unreadCount > 0 && (
                        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">
                          {unreadCount} unread
                        </span>
                      )}
                    </div>
                    {unreadCount > 0 && (
                      <button
                        onClick={handleMarkAllRead}
                        className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center space-x-1"
                        title="Mark all as read"
                      >
                        <CheckCheck className="w-3.5 h-3.5" />
                        <span>Read all</span>
                      </button>
                    )}
                  </div>

                  {/* Dropdown Body */}
                  <div className="max-h-80 overflow-y-auto divide-y divide-[#1E2E5C]/30">
                    {notifications.length === 0 ? (
                      <div className="p-6 text-center text-gray-400">
                        <Shield className="w-8 h-8 text-cyan-500/40 mx-auto mb-2" />
                        <p className="text-xs">No active security alerts.</p>
                        <p className="text-[10px] text-gray-500 mt-0.5">Your browsing environment is protected.</p>
                      </div>
                    ) : (
                      notifications.map((n) => {
                        const sev = (n.severity || 'LOW').toUpperCase();
                        const isCrit = sev === 'CRITICAL';
                        const isHigh = sev === 'HIGH';
                        const isMed = sev === 'MEDIUM';

                        return (
                          <div
                            key={n.id}
                            onClick={() => !n.is_read && handleMarkRead(n.id)}
                            className={`p-3 transition-colors cursor-pointer ${
                              n.is_read ? 'bg-[#080d1e] hover:bg-slate-800/30 opacity-75' : 'bg-slate-900/40 hover:bg-slate-800/60'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex items-start space-x-2">
                                {isCrit ? (
                                  <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                                ) : isHigh ? (
                                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                                ) : (
                                  <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                                )}
                                <div>
                                  <div className="flex items-center space-x-1.5 mb-1">
                                    <span
                                      className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded border ${
                                        isCrit
                                          ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                                          : isHigh
                                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                                          : isMed
                                          ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40'
                                          : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                                      }`}
                                    >
                                      {sev}
                                    </span>
                                    <span className="text-xs font-semibold text-gray-200 line-clamp-1">
                                      {n.title}
                                    </span>
                                  </div>
                                  <p className="text-[11px] text-gray-400 line-clamp-2 leading-relaxed">
                                    {n.message}
                                  </p>
                                  {n.target_domain && (
                                    <span className="text-[10px] font-mono text-cyan-400 block mt-1">
                                      {n.target_domain}
                                    </span>
                                  )}
                                </div>
                              </div>
                              {!n.is_read && (
                                <span className="h-2 w-2 rounded-full bg-cyan-400 shrink-0 mt-1" />
                              )}
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>

                  {/* Dropdown Footer */}
                  <div className="p-2 border-t border-[#1E2E5C]/60 bg-[#0d142d] text-center">
                    <button
                      onClick={() => {
                        setIsOpen(false);
                        setCurrentTab('dashboard');
                      }}
                      className="text-xs font-semibold text-[#00F0FF] hover:underline"
                    >
                      View All in Control Center &rarr;
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Mobile Navigation Row */}
        <div className="flex md:hidden items-center justify-around py-2 border-t border-[#1E2E5C]/40 text-xs">
          <button
            onClick={() => setCurrentTab('landing')}
            className={`px-2 py-1 rounded ${currentTab === 'landing' ? 'text-[#00F0FF] font-bold' : 'text-gray-400'}`}
          >
            Overview
          </button>
          <button
            onClick={() => setCurrentTab('dashboard')}
            className={`px-2 py-1 rounded ${currentTab === 'dashboard' ? 'text-[#00F0FF] font-bold' : 'text-gray-400'}`}
          >
            Control Center
          </button>
          <button
            onClick={() => setCurrentTab('modules')}
            className={`px-2 py-1 rounded ${currentTab === 'modules' ? 'text-[#00F0FF] font-bold' : 'text-gray-400'}`}
          >
            Modules
          </button>
          <button
            onClick={() => setCurrentTab('system')}
            className={`px-2 py-1 rounded ${currentTab === 'system' ? 'text-[#00F0FF] font-bold' : 'text-gray-400'}`}
          >
            System
          </button>
        </div>
      </div>
    </header>
  );
};
