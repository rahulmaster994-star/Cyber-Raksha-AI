import React, { useState } from 'react';
import { apiService } from '../services/api';
import type { UnifiedAnalyzeResponse } from '../services/api';

export const UnifiedThreatAnalyzerPage: React.FC = () => {
  const [urlInput, setUrlInput] = useState('');
  const [messageInput, setMessageInput] = useState('');
  const [isDigitalArrestFocus, setIsDigitalArrestFocus] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<UnifiedAnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim() && !messageInput.trim()) {
      setError('Please provide at least a URL or a message for multi-vector threat correlation.');
      return;
    }
    setError(null);
    setIsAnalyzing(true);
    setResult(null);

    const res = await apiService.analyzeUnified({
      url: urlInput.trim() || undefined,
      message: messageInput.trim() || undefined,
      is_digital_arrest: isDigitalArrestFocus,
    });
    setIsAnalyzing(false);

    if (res.error) {
      setError(res.error);
    } else if (res.data) {
      setResult(res.data);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
        return 'text-red-400 border-red-500/50 bg-red-950/20';
      case 'HIGH':
        return 'text-orange-400 border-orange-500/50 bg-orange-950/20';
      case 'MEDIUM':
        return 'text-amber-400 border-amber-500/50 bg-amber-950/20';
      default:
        return 'text-emerald-400 border-emerald-500/50 bg-emerald-950/20';
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="border border-cyan-500/30 bg-cyber-card/60 backdrop-blur-md rounded-2xl p-6 sm:p-8 relative overflow-hidden">
        <div className="absolute -right-12 -top-12 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium tracking-wide bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              UNIFIED CORRELATION ENGINE
            </span>
            <span className="text-xs font-mono text-gray-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              STAGE 5 ACTIVE
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold font-mono tracking-tight text-white mt-2">
            Cyber Raksha — Unified Threat Analyzer
          </h1>
          <p className="text-gray-400 text-sm mt-1 max-w-3xl">
            Simultaneously correlate phishing URLs, coercive message communications, Digital Arrest extortion signals,
            and threat intelligence feeds into a single unified threat verdict.
          </p>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Form Column */}
        <div className="lg:col-span-1 space-y-6">
          <div className="border border-gray-800 bg-cyber-card/40 rounded-xl p-6 backdrop-blur-sm space-y-5">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Multi-Vector Input
            </h2>

            <form onSubmit={handleAnalyze} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-gray-300 mb-1">
                  SUSPICIOUS URL (OPTIONAL)
                </label>
                <input
                  type="text"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://secure-login-hdfcbank.serveo.net"
                  className="w-full px-3.5 py-2.5 rounded-lg bg-cyber-bg/70 border border-gray-700 text-white font-mono text-xs focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-gray-300 mb-1">
                  SUSPICIOUS MESSAGE / EXTORTION TEXT
                </label>
                <textarea
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  rows={5}
                  placeholder="Paste SMS, WhatsApp message, email, or digital arrest notice..."
                  className="w-full px-3.5 py-2.5 rounded-lg bg-cyber-bg/70 border border-gray-700 text-white font-mono text-xs focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="da-focus"
                  checked={isDigitalArrestFocus}
                  onChange={(e) => setIsDigitalArrestFocus(e.target.checked)}
                  className="rounded border-gray-700 text-cyan-500 focus:ring-0"
                />
                <label htmlFor="da-focus" className="text-xs text-gray-300 font-mono">
                  Focus on Digital Arrest extortion patterns
                </label>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-950/30 border border-red-500/40 text-red-300 text-xs">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isAnalyzing}
                className={`w-full py-2.5 rounded-lg font-mono text-sm font-semibold tracking-wide transition-all ${
                  isAnalyzing
                    ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black shadow-lg shadow-cyan-500/20'
                }`}
              >
                {isAnalyzing ? 'Correlating Vectors...' : 'Run Unified Risk Assessment'}
              </button>
            </form>
          </div>
        </div>

        {/* Results Column */}
        <div className="lg:col-span-2 space-y-6">
          {result ? (
            <div className="border border-gray-800 bg-cyber-card/60 rounded-xl p-6 backdrop-blur-md space-y-6">
              {/* Verdict Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-800">
                <div>
                  <span className="text-xs font-mono text-gray-400 uppercase tracking-wider">Unified Threat Assessment</span>
                  <div className="flex items-center gap-3 mt-1">
                    <span className={`px-3 py-1 rounded-md font-mono text-sm font-bold border ${getRiskColor(result.overall_risk_level)}`}>
                      {result.overall_risk_level} RISK
                    </span>
                    <span className="text-xs text-gray-300 font-mono">
                      Category: <strong className="text-white">{result.threat_category}</strong>
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4 bg-cyber-bg/70 px-4 py-2.5 rounded-xl border border-gray-800">
                  <div className="text-right">
                    <div className="text-xs text-gray-400 font-mono">UNIFIED SCORE</div>
                    <div className="text-2xl font-mono font-bold text-white">
                      {result.overall_risk_score}<span className="text-xs text-gray-500">/100</span>
                    </div>
                  </div>
                  <div className="w-12 h-12 rounded-full border-2 border-cyan-500/40 flex items-center justify-center font-mono text-xs text-cyan-300">
                    {result.overall_risk_score}%
                  </div>
                </div>
              </div>

              {/* Corroboration Alert */}
              {result.is_corroborated && (
                <div className="p-3.5 rounded-lg bg-cyan-950/30 border border-cyan-500/40 text-cyan-300 text-xs font-mono space-y-1">
                  <div className="font-bold flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-cyan-400" />
                    CROSS-VECTOR CORROBORATION CONFIRMED (+15 Boost)
                  </div>
                  <ul className="list-disc pl-5 space-y-0.5 text-gray-300">
                    {result.corroboration_notes.map((note, idx) => (
                      <li key={idx}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Explanation */}
              <div className="p-4 rounded-lg bg-cyber-bg/40 border border-gray-800 text-sm text-gray-300 leading-relaxed">
                <h4 className="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1">Evidence Justification</h4>
                <p>{result.explanation}</p>
              </div>

              {/* Evidence Chain */}
              {result.evidence_chain.length > 0 && (
                <div>
                  <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400 mb-3">
                    Multi-Vector Evidence Chain ({result.evidence_chain.length})
                  </h3>
                  <div className="space-y-2">
                    {result.evidence_chain.map((ev, i) => (
                      <div key={i} className="p-3 rounded-lg bg-cyber-bg/40 border border-gray-800 flex items-start justify-between gap-4">
                        <div>
                          <div className="text-xs font-mono font-bold text-white">{ev.title}</div>
                          <div className="text-xs text-gray-400 mt-0.5">{ev.details}</div>
                          <div className="text-[10px] text-cyan-400 font-mono mt-1">Source: {ev.source}</div>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border shrink-0 ${getRiskColor(ev.severity)}`}>
                          {ev.severity}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Actions */}
              <div>
                <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400 mb-2">Recommended Defensive Actions</h3>
                <ul className="space-y-1.5">
                  {result.recommended_actions.map((rec, i) => (
                    <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                      <span className="text-cyan-400 font-bold">›</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="border border-gray-800 bg-cyber-card/40 rounded-xl p-12 text-center text-gray-500 font-mono text-xs">
              Provide input in the left panel to execute unified multi-vector risk correlation.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
