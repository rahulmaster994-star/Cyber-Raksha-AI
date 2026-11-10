import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import type {
  ThreatIndicator,
  ThreatIntelStatusResponse,
  ThreatSearchResponse,
  LiveThreatEvent,
} from '../services/api';

export const ThreatIntelPage: React.FC = () => {
  const [status, setStatus] = useState<ThreatIntelStatusResponse | null>(null);
  const [indicators, setIndicators] = useState<ThreatIndicator[]>([]);
  const [events, setEvents] = useState<LiveThreatEvent[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResult, setSearchResult] = useState<ThreatSearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isUpdatingFeed, setIsUpdatingFeed] = useState(false);
  const [feedUpdateMessage, setFeedUpdateMessage] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadLiveEvents, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    const [stRes, indRes, evRes] = await Promise.all([
      apiService.getIntelStatus(),
      apiService.getVerifiedIndicators(50),
      apiService.getLiveEvents(20),
    ]);
    if (stRes.data) setStatus(stRes.data);
    if (indRes.data) setIndicators(indRes.data);
    if (evRes.data) setEvents(evRes.data);
  };

  const loadLiveEvents = async () => {
    const res = await apiService.getLiveEvents(20);
    if (res.data) setEvents(res.data);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    setSearchResult(null);

    const res = await apiService.searchThreatIndicator(searchQuery.trim());
    setIsSearching(false);
    if (res.data) {
      setSearchResult(res.data);
    }
  };

  const handleFeedUpdate = async () => {
    setIsUpdatingFeed(true);
    setFeedUpdateMessage(null);
    const res = await apiService.triggerFeedUpdate();
    setIsUpdatingFeed(false);
    if (res.data) {
      setFeedUpdateMessage(
        `Feed updated: ${res.data.records_added || 0} indicators ingested from ${res.data.source || 'URLhaus'} in ${res.data.duration_seconds || 0}s.`
      );
      loadData();
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

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="border border-cyan-500/30 bg-cyber-card/60 backdrop-blur-md rounded-2xl p-6 sm:p-8 relative overflow-hidden">
        <div className="absolute -right-12 -top-12 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium tracking-wide bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                STAGE 5 INTELLIGENCE
              </span>
              <span className="text-xs font-mono text-gray-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                IoC FEEDS SYNCHRONIZED
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold font-mono tracking-tight text-white mt-2">
              Threat Intelligence Center
            </h1>
            <p className="text-gray-400 text-sm mt-1 max-w-2xl">
              Real-time threat feed ingestion, IoC correlation engine, and indicators database aggregating URLhaus,
              PhishTank, OpenPhish, and CERT-In advisories.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleFeedUpdate}
              disabled={isUpdatingFeed}
              className={`px-4 py-2 rounded-lg font-mono text-xs font-semibold tracking-wide border transition-all ${
                isUpdatingFeed
                  ? 'bg-gray-800 text-gray-500 border-gray-700 cursor-not-allowed'
                  : 'bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border-cyan-500/40'
              }`}
            >
              {isUpdatingFeed ? 'Pulling Feed...' : 'Sync Threat Feeds'}
            </button>
          </div>
        </div>
      </div>

      {feedUpdateMessage && (
        <div className="p-3 rounded-lg bg-cyan-950/30 border border-cyan-500/40 text-cyan-300 text-xs font-mono">
          {feedUpdateMessage}
        </div>
      )}

      {/* Telemetry Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-cyber-card/40 border border-gray-800 backdrop-blur-sm">
          <div className="text-xs font-mono text-gray-400">ACTIVE INDICATORS</div>
          <div className="text-2xl font-mono font-bold text-white mt-1">
            {status?.total_active_indicators || indicators.length}
          </div>
          <div className="text-[10px] text-cyan-400 font-mono mt-1">Indexed in-memory</div>
        </div>
        <div className="p-4 rounded-xl bg-cyber-card/40 border border-gray-800 backdrop-blur-sm">
          <div className="text-xs font-mono text-gray-400">INTELLIGENCE SOURCES</div>
          <div className="text-2xl font-mono font-bold text-white mt-1">
            {status?.sources?.length || 4}
          </div>
          <div className="text-[10px] text-emerald-400 font-mono mt-1">URLhaus, PhishTank, CERT-In</div>
        </div>
        <div className="p-4 rounded-xl bg-cyber-card/40 border border-gray-800 backdrop-blur-sm">
          <div className="text-xs font-mono text-gray-400">SECURITY EVENTS LOGGED</div>
          <div className="text-2xl font-mono font-bold text-white mt-1">{events.length}</div>
          <div className="text-[10px] text-purple-400 font-mono mt-1">Live audit stream</div>
        </div>
        <div className="p-4 rounded-xl bg-cyber-card/40 border border-gray-800 backdrop-blur-sm">
          <div className="text-xs font-mono text-gray-400">ENGINE STATUS</div>
          <div className="text-2xl font-mono font-bold text-emerald-400 mt-1">ACTIVE</div>
          <div className="text-[10px] text-gray-400 font-mono mt-1">Cross-vector correlation</div>
        </div>
      </div>

      {/* IoC Search Explorer */}
      <div className="border border-gray-800 bg-cyber-card/40 rounded-xl p-6 backdrop-blur-sm space-y-4">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          Threat Explorer — IoC Reputation & Feed Lookup
        </h2>
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search suspicious URL, domain (e.g. secure-login-hdfcbank.serveo.net), or IP address..."
            className="flex-1 px-4 py-2.5 rounded-lg bg-cyber-bg/70 border border-gray-700 text-white font-mono text-sm focus:outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            disabled={isSearching || !searchQuery.trim()}
            className="px-6 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-mono font-semibold text-sm transition-all"
          >
            {isSearching ? 'Searching...' : 'Search IoC'}
          </button>
        </form>

        {/* Search Result Card */}
        {searchResult && (
          <div className={`p-4 rounded-xl border mt-4 ${
            searchResult.is_threat_found
              ? 'bg-red-950/20 border-red-500/50'
              : 'bg-emerald-950/20 border-emerald-500/50'
          }`}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-gray-800">
              <div className="flex items-center gap-3">
                <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${getSeverityBadge(searchResult.severity || 'LOW')}`}>
                  {searchResult.is_threat_found ? `${searchResult.severity} THREAT FOUND` : 'NO KNOWN THREAT'}
                </span>
                <span className="text-xs font-mono text-gray-300">{searchResult.query}</span>
              </div>
              {searchResult.source && (
                <span className="text-xs font-mono text-cyan-400">
                  SOURCE: <strong>{searchResult.source}</strong>
                </span>
              )}
            </div>

            {searchResult.matched_indicator && (
              <div className="mt-3 text-xs space-y-1 text-gray-300 font-mono">
                <div>Type: <span className="text-white">{searchResult.matched_indicator.threat_type}</span></div>
                <div>Description: <span className="text-gray-400">{searchResult.matched_indicator.description}</span></div>
                {searchResult.matched_indicator.source_reference && (
                  <div>Reference: <span className="text-cyan-400">{searchResult.matched_indicator.source_reference}</span></div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Main Two-Column View: Verified Indicators Table & Live Event Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Verified IoCs Table */}
        <div className="lg:col-span-2 border border-gray-800 bg-cyber-card/40 rounded-xl p-5 backdrop-blur-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-mono uppercase tracking-wider text-white font-semibold">
              Verified Threat Intelligence Indicators ({indicators.length})
            </h3>
            <span className="text-xs font-mono text-gray-400">Cached In-Memory</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="text-gray-400 border-b border-gray-800 pb-2">
                <tr>
                  <th className="py-2">TYPE</th>
                  <th className="py-2">INDICATOR</th>
                  <th className="py-2">CATEGORY</th>
                  <th className="py-2">SOURCE</th>
                  <th className="py-2">SEVERITY</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {indicators.map((ioc, idx) => (
                  <tr key={idx} className="hover:bg-cyber-bg/40 transition-colors">
                    <td className="py-2 text-cyan-400">{ioc.indicator_type}</td>
                    <td className="py-2 text-white truncate max-w-[200px]" title={ioc.indicator_value}>
                      {ioc.indicator_value}
                    </td>
                    <td className="py-2 text-gray-300">{ioc.threat_type}</td>
                    <td className="py-2 text-gray-400">{ioc.source_name}</td>
                    <td className="py-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getSeverityBadge(ioc.severity)}`}>
                        {ioc.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live Event Stream */}
        <div className="border border-gray-800 bg-cyber-card/40 rounded-xl p-5 backdrop-blur-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-mono uppercase tracking-wider text-white font-semibold flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Live Security Event Stream
            </h3>
            <span className="text-[10px] font-mono text-gray-400">{events.length} events</span>
          </div>

          {events.length > 0 ? (
            <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
              {events.map((ev) => (
                <div key={ev.id} className="p-3 rounded-lg bg-cyber-bg/60 border border-gray-800/80 text-xs space-y-1">
                  <div className="flex items-center justify-between font-mono">
                    <span className="text-cyan-400 font-semibold">{ev.event_type}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${getSeverityBadge(ev.severity)}`}>
                      {ev.severity}
                    </span>
                  </div>
                  <p className="text-gray-300 text-xs leading-relaxed">{ev.description}</p>
                  <div className="text-[10px] text-gray-500 font-mono flex items-center justify-between pt-1">
                    <span>{ev.source_component}</span>
                    <span>{new Date(ev.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-500 text-center py-8 font-mono">
              No security events recorded yet. Perform a unified analysis to generate events.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
