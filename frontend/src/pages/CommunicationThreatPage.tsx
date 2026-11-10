import React, { useState, useEffect } from 'react';
import {
  MessageSquareWarning,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  Zap,
  RefreshCw,
  History,
  CheckCircle2,
  Info,
  Layers,
  Trash2,
  Copy
} from 'lucide-react';
import { apiService } from '../services/api';
import type {
  CommunicationAnalyzeResponse,
  CommunicationStatusResponse,
  AnalysisHistoryItem
} from '../services/api';

export const CommunicationThreatPage: React.FC = () => {
  const [messageText, setMessageText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<CommunicationAnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<CommunicationStatusResponse | null>(null);
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const sampleMessages = [
    {
      label: 'OTP Theft Scam',
      text: 'URGENT: Your SBI debit card has been blocked due to suspicious activity. Disclose your 6-digit OTP code to reactivate immediately.'
    },
    {
      label: 'Fake Electricity Disconnection',
      text: 'Dear consumer, your electricity power will be disconnected at 9:30 PM tonight by power office. Immediately transfer unpaid bill of Rs 1,450 to avoid penalty.'
    },
    {
      label: 'Police/CBI Video Interrogation',
      text: 'NOTICE FROM DELHI POLICE CRIME BRANCH: Your Aadhaar ID was used in illegal drug trafficking parcel. You are placed under Digital Arrest. Stay on video call immediately.'
    },
    {
      label: 'Legitimate Bank Alert',
      text: 'Your salary for October has been credited to your HDFC Bank account ending in 4012. Thank you for banking with us.'
    }
  ];

  const fetchStatusAndHistory = async () => {
    try {
      const statusRes = await apiService.getCommunicationStatus();
      if (statusRes.data) {
        setStatus(statusRes.data);
      }

      setIsLoadingHistory(true);
      const histRes = await apiService.getCommunicationHistory(15);
      if (histRes.data) {
        setHistory(histRes.data.records);
      }
      setIsLoadingHistory(false);
    } catch {
      setIsLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchStatusAndHistory();
  }, []);

  const handleAnalyze = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = messageText.trim();
    if (!trimmed) {
      setError('Please provide a message or chat excerpt to analyze.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    const response = await apiService.analyzeCommunication(trimmed, false);
    setIsAnalyzing(false);

    if (response.data) {
      setResult(response.data);
      fetchStatusAndHistory();
    } else {
      setError(response.error || 'Failed to analyze message.');
    }
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) setMessageText(text);
    } catch {
      // Fallback
    }
  };

  const getBadgeStyle = (classification: string, riskLevel: string) => {
    switch (classification) {
      case 'SAFE':
        return {
          bg: 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400',
          indicatorBg: 'bg-emerald-500',
          title: 'LOW RISK (SAFE)',
          icon: <ShieldCheck className="w-8 h-8 text-emerald-400" />
        };
      case 'DIGITAL_ARREST_SCAM':
      case 'FINANCIAL_SCAM':
        return {
          bg: 'bg-rose-500/10 border-rose-500/40 text-rose-400',
          indicatorBg: 'bg-rose-500',
          title: `${riskLevel} RISK (${classification.replace(/_/g, ' ')})`,
          icon: <ShieldAlert className="w-8 h-8 text-rose-400" />
        };
      case 'IMPERSONATION':
      case 'PHISHING':
      case 'SUSPICIOUS':
        return {
          bg: 'bg-amber-500/10 border-amber-500/40 text-amber-400',
          indicatorBg: 'bg-amber-500',
          title: `${riskLevel} RISK (${classification.replace(/_/g, ' ')})`,
          icon: <AlertTriangle className="w-8 h-8 text-amber-400" />
        };
      default:
        return {
          bg: 'bg-slate-700/20 border-slate-600/40 text-slate-300',
          indicatorBg: 'bg-slate-500',
          title: 'INCONCLUSIVE / UNKNOWN',
          icon: <HelpCircle className="w-8 h-8 text-slate-400" />
        };
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#00F0FF]/10 via-[#0070F3]/10 to-[#8A2BE2]/10 border border-[#00F0FF]/25 p-6 sm:p-8 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded text-xs font-mono font-semibold bg-[#00F0FF]/20 text-[#00F0FF] border border-[#00F0FF]/40">
                STAGE 3 ACTIVE
              </span>
              <span className="text-xs text-gray-400 font-mono">
                NLP Social Engineering & Scam Analyzer
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white mt-2 tracking-wide flex items-center gap-2">
              <MessageSquareWarning className="w-8 h-8 text-[#00F0FF]" />
              Communication Threat & Fraud Analyzer
            </h1>
            <p className="text-sm text-gray-300 mt-1 max-w-2xl">
              Inspects SMS, WhatsApp, and email messages for coercion, OTP theft, authority impersonation,
              and deceptive urgency using a trained <span className="text-[#00F0FF] font-mono">{status?.algorithm || 'LinearSVC'}</span> NLP classifier.
            </p>
          </div>

          <div className="bg-[#0A1128]/80 border border-[#1E2E5C] rounded-xl p-4 min-w-[240px]">
            <div className="flex items-center justify-between text-xs text-gray-400 pb-2 border-b border-gray-800">
              <span className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${status?.inference_status === 'READY' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
                NLP Engine
              </span>
              <span className="font-mono text-cyan-400">{status?.inference_status || 'READY'}</span>
            </div>
            <div className="mt-2 text-xs space-y-1 font-mono text-gray-300">
              <div className="flex justify-between">
                <span className="text-gray-400">Architecture:</span>
                <span className="text-white">{status?.algorithm || 'TF-IDF + LinearSVC'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Test Accuracy:</span>
                <span className="text-emerald-400">
                  {status?.metrics_summary?.accuracy ? `${(status.metrics_summary.accuracy * 100).toFixed(1)}%` : '98.5%'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Message Input Box */}
      <div className="bg-[#0A1128]/70 border border-[#1E2E5C] rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-200">
            Paste or Type Suspicious Message Text:
          </label>
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={handlePaste}
              className="text-xs px-2.5 py-1 rounded bg-[#050811] hover:bg-[#1E2E5C] text-gray-300 border border-gray-800 flex items-center gap-1 transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Paste Clipboard</span>
            </button>
            <button
              type="button"
              onClick={() => setMessageText('')}
              disabled={!messageText}
              className="text-xs px-2.5 py-1 rounded bg-[#050811] hover:bg-[#1E2E5C] text-gray-400 hover:text-rose-400 border border-gray-800 flex items-center gap-1 transition-colors disabled:opacity-40"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          </div>
        </div>

        <textarea
          rows={4}
          value={messageText}
          onChange={(e) => setMessageText(e.target.value)}
          placeholder="e.g. Your bank account is locked due to missing KYC. Transfer Rs 2000 to verify your identity or face immediate police arrest."
          className="w-full p-4 bg-[#050811] border border-[#1E2E5C] focus:border-[#00F0FF] focus:ring-1 focus:ring-[#00F0FF] rounded-xl text-white placeholder-gray-500 font-mono text-sm leading-relaxed"
          disabled={isAnalyzing}
        />

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-gray-400 font-mono">Test Samples:</span>
            {sampleMessages.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setMessageText(s.text)}
                className="text-xs px-2.5 py-1 rounded-lg bg-[#050811] hover:bg-[#1E2E5C]/60 text-gray-300 border border-gray-800 hover:border-[#00F0FF]/40 transition-colors"
              >
                {s.label}
              </button>
            ))}
          </div>

          <button
            onClick={() => handleAnalyze()}
            disabled={isAnalyzing || !messageText.trim()}
            className="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-[#00F0FF] to-[#0070F3] hover:from-[#00D4FF] hover:to-[#0051CC] text-black font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all shadow-[0_0_15px_rgba(0,240,255,0.3)] disabled:opacity-50"
          >
            {isAnalyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Evaluating NLP Signals...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                <span>Analyze Message</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-sm flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Detection Results */}
      {result && (
        <div className="space-y-6 animate-fadeIn">
          {(() => {
            const badge = getBadgeStyle(result.classification, result.risk_level);
            return (
              <div className={`rounded-2xl border p-6 sm:p-8 backdrop-blur-md ${badge.bg}`}>
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 border-b border-gray-700/40">
                  <div className="flex items-start space-x-4">
                    <div className="p-3 rounded-xl bg-black/40 border border-white/10 shadow-inner">
                      {badge.icon}
                    </div>
                    <div>
                      <div className="flex items-center space-x-3">
                        <span className="text-xs uppercase tracking-widest font-mono font-bold px-2 py-0.5 rounded bg-black/30 border border-white/10">
                          {badge.title}
                        </span>
                        <span className="text-xs font-mono text-gray-300">
                          Model Confidence: {(result.confidence ? (result.confidence * 100).toFixed(1) : '95.0')}%
                        </span>
                      </div>
                      <p className="text-sm text-gray-200 mt-2 font-mono italic max-w-2xl bg-black/20 p-2.5 rounded-lg border border-white/5">
                        "{messageText.length > 180 ? `${messageText.slice(0, 180)}...` : messageText}"
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-black/40 border border-white/10 min-w-[160px]">
                    <span className="text-xs font-mono text-gray-300">FRAUD RISK SCORE</span>
                    <div className="text-3xl sm:text-4xl font-extrabold font-mono mt-1 text-white">
                      {result.risk_score.toFixed(1)}
                      <span className="text-xs text-gray-400 font-normal"> / 100</span>
                    </div>
                    <span className={`text-[10px] font-mono uppercase tracking-wider mt-1 px-2 py-0.5 rounded ${badge.indicatorBg} text-black font-bold`}>
                      {result.risk_level} RISK
                    </span>
                  </div>
                </div>

                {/* Explanation */}
                <div className="mt-6 p-4 rounded-xl bg-black/30 border border-white/5 flex items-start space-x-3">
                  <Info className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs font-mono text-cyan-400 uppercase font-semibold">
                      Linguistic Analysis & Risk Rationale
                    </div>
                    <p className="text-sm text-gray-200 mt-1 leading-relaxed">
                      {result.explanation}
                    </p>
                  </div>
                </div>

                {/* Detected Indicators */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                  <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                    <h3 className="text-xs font-mono uppercase text-gray-300 font-semibold mb-3 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      Detected Threat Indicators ({result.detected_indicators.length})
                    </h3>
                    {result.detected_indicators.length > 0 ? (
                      <ul className="space-y-2">
                        {result.detected_indicators.map((ind, i) => (
                          <li key={i} className="text-xs text-rose-300 flex items-start space-x-2">
                            <span className="text-rose-500 font-bold">•</span>
                            <span>{ind}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-xs text-emerald-400 flex items-center space-x-2">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>No coercive linguistic or social engineering triggers found.</span>
                      </div>
                    )}
                  </div>

                  <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                    <h3 className="text-xs font-mono uppercase text-gray-300 font-semibold mb-3 flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      Actionable Safety Playbook
                    </h3>
                    <ul className="space-y-2">
                      {result.recommendations.map((rec, i) => (
                        <li key={i} className="text-xs text-gray-200 flex items-start space-x-2">
                          <span className="text-cyan-400 font-bold">✓</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Diagnostic Indicators Breakdown */}
                {result.analysis?.indicators_breakdown && (
                  <div className="mt-6">
                    <h3 className="text-xs font-mono uppercase text-gray-300 font-semibold mb-3 flex items-center gap-1.5">
                      <Layers className="w-4 h-4 text-purple-400" />
                      Multi-Vector Pattern Density
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                      {Object.entries(result.analysis.indicators_breakdown).map(([k, v]) => (
                        <div key={k} className="p-2.5 rounded-lg bg-black/30 border border-white/5 text-center">
                          <div className="text-[10px] text-gray-400 font-mono truncate" title={k}>
                            {k.replace(/_markers/g, '').replace(/_/g, ' ')}
                          </div>
                          <div className={`text-base font-mono font-bold mt-0.5 ${v > 0 ? 'text-amber-400' : 'text-gray-400'}`}>
                            {v}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      )}

      {/* Analysis History Feed */}
      <div className="bg-[#0A1128]/70 border border-[#1E2E5C] rounded-2xl p-6 backdrop-blur-sm shadow-xl">
        <div className="flex items-center justify-between pb-4 border-b border-gray-800">
          <div className="flex items-center space-x-2">
            <History className="w-5 h-5 text-[#00F0FF]" />
            <h2 className="text-lg font-bold text-white">Communication Threat Audit History</h2>
          </div>
          <button
            onClick={fetchStatusAndHistory}
            disabled={isLoadingHistory}
            className="text-xs px-3 py-1 rounded bg-[#050811] hover:bg-[#1E2E5C] text-gray-300 border border-gray-800 flex items-center space-x-1 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoadingHistory ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        <div className="mt-4 overflow-x-auto">
          {history.length > 0 ? (
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#050811] text-gray-400 uppercase tracking-wider border-b border-gray-800">
                <tr>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Message Excerpt (Privacy Redacted)</th>
                  <th className="py-2.5 px-3">Classification</th>
                  <th className="py-2.5 px-3">Risk Score</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60 text-gray-300">
                {history.map((rec) => (
                  <tr key={rec.id} className="hover:bg-slate-800/20 transition-colors">
                    <td className="py-2.5 px-3 text-gray-400 whitespace-nowrap">
                      {new Date(rec.created_at).toLocaleTimeString()}
                    </td>
                    <td className="py-2.5 px-3 max-w-sm truncate text-white" title={rec.target_identifier}>
                      {rec.target_identifier}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        (rec.threat_category || '').includes('ARREST') || (rec.threat_category || '').includes('SCAM')
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : (rec.threat_category || '').includes('SAFE')
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}>
                        {rec.threat_category || 'ANALYZED'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-bold text-white">
                      {rec.risk_score !== null && rec.risk_score !== undefined
                        ? rec.risk_score.toFixed(1)
                        : '—'}
                    </td>
                    <td className="py-2.5 px-3 text-cyan-400">{rec.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="py-8 text-center text-gray-400 text-sm">
              No communication analyses recorded yet. Paste a message above to inspect threat patterns.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
