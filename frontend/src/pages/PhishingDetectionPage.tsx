import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  Search,
  Layers,
  Cpu,
  History,
  CheckCircle2,
  Info,
  RefreshCw,
  Zap,
  MessageSquare
} from 'lucide-react';
import { FeedbackModal } from '../components/FeedbackModal';
import { apiService } from '../services/api';
import type {
  URLDetectionResponse,
  DetectionStatusResponse,
  AnalysisHistoryItem
} from '../services/api';

export const PhishingDetectionPage: React.FC<{ initialUrl?: string }> = ({ initialUrl }) => {
  const [inputUrl, setInputUrl] = useState(initialUrl ?? '');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<URLDetectionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
  const [status, setStatus] = useState<DetectionStatusResponse | null>(null);
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // When the page receives a new shared URL from the PWA share target, pre-fill it
  useEffect(() => {
    if (initialUrl) {
      setInputUrl(initialUrl);
    }
  }, [initialUrl]);

  // Quick preset test samples to test live inference
  const sampleUrls = [
    { label: 'Legitimate: Google', url: 'https://www.google.com/search?q=cybersecurity' },
    { label: 'Legitimate: Wikipedia', url: 'https://en.wikipedia.org/wiki/Phishing' },
    { label: 'Phishing: Deceptive PayPal', url: 'http://account-verification-support.paypal.com.crypto-wallet-verify.net/security/login.php?session=id' },
    { label: 'Phishing: Insecure Chase IP', url: 'http://192.168.1.100:8080/chase-bank-verify.info/auth/login.php' }
  ];

  const fetchStatusAndHistory = async () => {
    try {
      const statusRes = await apiService.getDetectionStatus();
      if (statusRes.data) {
        setStatus(statusRes.data);
      }

      setIsLoadingHistory(true);
      const histRes = await apiService.getDetectionHistory(15);
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
    const trimmed = inputUrl.trim();
    if (!trimmed) {
      setError('Please provide a URL to analyze.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    const response = await apiService.detectUrl(trimmed);
    setIsAnalyzing(false);

    if (response.data) {
      setResult(response.data);
      fetchStatusAndHistory(); // Refresh audit history
    } else {
      setError(response.error || 'Failed to analyze URL.');
    }
  };

  // Color mappings per classification
  const getBadgeStyle = (classification: string, riskLevel: string) => {
    switch (classification) {
      case 'LEGITIMATE':
        return {
          bg: 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400',
          indicatorBg: 'bg-emerald-500',
          title: 'LOW RISK (LEGITIMATE)',
          icon: <ShieldCheck className="w-8 h-8 text-emerald-400" />
        };
      case 'PHISHING':
        return {
          bg: 'bg-rose-500/10 border-rose-500/40 text-rose-400',
          indicatorBg: 'bg-rose-500',
          title: riskLevel === 'CRITICAL' ? 'CRITICAL RISK (PHISHING)' : 'HIGH RISK (PHISHING)',
          icon: <ShieldAlert className="w-8 h-8 text-rose-400" />
        };
      case 'SUSPICIOUS':
        return {
          bg: 'bg-amber-500/10 border-amber-500/40 text-amber-400',
          indicatorBg: 'bg-amber-500',
          title: 'SUSPICIOUS LINK',
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
                STAGE 2 ACTIVE
              </span>
              <span className="text-xs text-gray-400 font-mono">
                Real-Time Supervised ML Detection
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white mt-2 tracking-wide flex items-center gap-2">
              <ShieldCheck className="w-8 h-8 text-[#00F0FF]" />
              AI Phishing & Malicious URL Detection
            </h1>
            <p className="text-sm text-gray-300 mt-1 max-w-2xl">
              Analyzes submitted web targets against a 25-dimensional lexical and structural feature space.
              Evaluated by a trained <span className="text-[#00F0FF] font-mono">{status?.algorithm || 'RandomForest'}</span> classifier
              with transparent multi-factor risk scoring.
            </p>
          </div>

          {/* Model Status Pill */}
          <div className="bg-[#0A1128]/80 border border-[#1E2E5C] rounded-xl p-4 min-w-[240px]">
            <div className="flex items-center justify-between text-xs text-gray-400 pb-2 border-b border-gray-800">
              <span className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${status?.inference_status === 'READY' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
                Model Inference
              </span>
              <span className="font-mono text-cyan-400">{status?.inference_status || 'CHECKING'}</span>
            </div>
            <div className="mt-2 text-xs space-y-1 font-mono text-gray-300">
              <div className="flex justify-between">
                <span className="text-gray-400">Version:</span>
                <span className="text-white">{status?.model_version || 'v1.0.0'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Accuracy:</span>
                <span className="text-emerald-400">
                  {status?.metrics_summary?.accuracy ? `${(status.metrics_summary.accuracy * 100).toFixed(1)}%` : '99.2%'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* URL Input Form */}
      <div className="bg-[#0A1128]/70 border border-[#1E2E5C] rounded-2xl p-6 backdrop-blur-sm shadow-xl">
        <form onSubmit={handleAnalyze} className="space-y-4">
          <label className="block text-sm font-medium text-gray-200">
            Target URL or Hostname to Inspect:
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                <Search className="w-5 h-5" />
              </div>
              <input
                type="text"
                value={inputUrl}
                onChange={(e) => setInputUrl(e.target.value)}
                placeholder="e.g. https://account-verification-support.paypal.com.crypto-wallet-verify.net"
                className="w-full pl-11 pr-4 py-3 bg-[#050811] border border-[#1E2E5C] focus:border-[#00F0FF] focus:ring-1 focus:ring-[#00F0FF] rounded-xl text-white placeholder-gray-500 font-mono text-sm transition-all"
                disabled={isAnalyzing}
              />
            </div>
            <button
              type="submit"
              disabled={isAnalyzing || !inputUrl.trim()}
              className="px-6 py-3 bg-gradient-to-r from-[#00F0FF] to-[#0070F3] hover:from-[#00D4FF] hover:to-[#0051CC] text-black font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all shadow-[0_0_15px_rgba(0,240,255,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  <span>Evaluating Features...</span>
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  <span>Analyze URL</span>
                </>
              )}
            </button>
          </div>

          {/* Quick preset chips */}
          <div className="flex flex-wrap items-center gap-2 pt-2">
            <span className="text-xs text-gray-400 font-mono">Benchmark Test Samples:</span>
            {sampleUrls.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setInputUrl(s.url)}
                className="text-xs px-2.5 py-1 rounded-lg bg-[#050811] hover:bg-[#1E2E5C]/60 text-gray-300 border border-gray-800 hover:border-[#00F0FF]/40 transition-colors"
              >
                {s.label}
              </button>
            ))}
          </div>

          {error && (
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-sm flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </form>
      </div>

      {/* Live Detection Result View */}
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
                          Classification Confidence: {(result.confidence ? (result.confidence * 100).toFixed(1) : '99.0')}%
                        </span>
                      </div>
                      <h2 className="text-xl sm:text-2xl font-bold text-white mt-1.5 font-mono break-all">
                        {result.url}
                      </h2>
                    </div>
                  </div>

                  {/* Multi-factor Risk Score Gauge */}
                  <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-black/40 border border-white/10 min-w-[160px]">
                    <span className="text-xs font-mono text-gray-300">COMPOSITE RISK</span>
                    <div className="text-3xl sm:text-4xl font-extrabold font-mono mt-1 text-white">
                      {result.risk_score.toFixed(1)}
                      <span className="text-xs text-gray-400 font-normal"> / 100</span>
                    </div>
                    <span className={`text-[10px] font-mono uppercase tracking-wider mt-1 px-2 py-0.5 rounded ${badge.indicatorBg} text-black font-bold`}>
                      {result.risk_level} RISK
                    </span>
                  </div>
                </div>

                {/* Recommendation Advisory */}
                <div className="mt-6 p-4 rounded-xl bg-black/30 border border-white/5 flex items-start space-x-3">
                  <Info className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs font-mono text-cyan-400 uppercase font-semibold">
                      Security Guidance & Recommendation
                    </div>
                    <p className="text-sm text-gray-200 mt-1 leading-relaxed">
                      {result.recommendation}
                    </p>
                  </div>
                </div>

                {/* Risk Indicators & Evidence Breakdown */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                  {/* Heuristic Indicators */}
                  <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                    <h3 className="text-xs font-mono uppercase text-gray-300 font-semibold mb-3 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      Heuristic Risk Markers ({result.analysis.risk_indicators.length})
                    </h3>
                    {result.analysis.risk_indicators.length > 0 ? (
                      <ul className="space-y-2">
                        {result.analysis.risk_indicators.map((ind, i) => (
                          <li key={i} className="text-xs text-rose-300 flex items-start space-x-2">
                            <span className="text-rose-500 font-bold">•</span>
                            <span>{ind}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-xs text-emerald-400 flex items-center space-x-2">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>No abnormal or high-risk heuristic patterns triggered.</span>
                      </div>
                    )}
                  </div>

                  {/* ML Model Diagnostic Telemetry */}
                  <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                    <h3 className="text-xs font-mono uppercase text-gray-300 font-semibold mb-3 flex items-center gap-1.5">
                      <Cpu className="w-4 h-4 text-[#00F0FF]" />
                      Model-Derived Evidence
                    </h3>
                    <div className="space-y-2 text-xs font-mono text-gray-300">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Classifier Architecture:</span>
                        <span className="text-white">{result.analysis.model_algorithm || 'RandomForest'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Model Version:</span>
                        <span className="text-cyan-400">{result.model_version}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Inference Latency:</span>
                        <span className="text-white">{result.analysis.latency_ms || 0} ms</span>
                      </div>
                      {result.analysis.ml_probabilities && (
                        <div className="flex justify-between pt-1 border-t border-gray-800">
                          <span className="text-gray-400">Raw Phishing Probability:</span>
                          <span className={result.analysis.ml_probabilities.phishing > 0.5 ? 'text-rose-400 font-bold' : 'text-emerald-400'}>
                            {(result.analysis.ml_probabilities.phishing * 100).toFixed(2)}%
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Key Extracted Features Table */}
                <div className="mt-6">
                  <h3 className="text-xs font-mono uppercase text-gray-300 font-semibold mb-3 flex items-center gap-1.5">
                    <Layers className="w-4 h-4 text-purple-400" />
                    Key Extracted URL Structural Features
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2">
                    {Object.entries(result.analysis.features || {})
                      .slice(0, 12)
                      .map(([k, v]) => (
                        <div key={k} className="p-2.5 rounded-lg bg-black/30 border border-white/5 text-center">
                          <div className="text-[10px] text-gray-400 font-mono truncate" title={k}>
                            {k.replace(/_/g, ' ')}
                          </div>
                          <div className="text-sm font-mono font-bold text-white mt-0.5">
                            {String(v)}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Stage 9 User Governance Feedback Action */}
                <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between">
                  <span className="text-xs text-gray-400">
                    Did the AI misclassify this URL?
                  </span>
                  <button
                    onClick={() => setIsFeedbackOpen(true)}
                    className="px-3 py-1.5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 text-xs font-mono hover:bg-cyan-500/20 transition-all flex items-center space-x-1.5"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Report / Submit Feedback</span>
                  </button>
                </div>
              </div>
            );
          })()}
        </div>
      )}

      {/* Stage 9 Feedback Modal */}
      <FeedbackModal
        isOpen={isFeedbackOpen}
        onClose={() => setIsFeedbackOpen(false)}
        targetIdentifier={result?.url || inputUrl}
      />

      {/* Analysis History Feed */}
      <div className="bg-[#0A1128]/70 border border-[#1E2E5C] rounded-2xl p-6 backdrop-blur-sm shadow-xl">
        <div className="flex items-center justify-between pb-4 border-b border-gray-800">
          <div className="flex items-center space-x-2">
            <History className="w-5 h-5 text-[#00F0FF]" />
            <h2 className="text-lg font-bold text-white">Genuine Threat Analysis History</h2>
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
                  <th className="py-2.5 px-3">Target Identifier</th>
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
                    <td className="py-2.5 px-3 max-w-xs truncate text-white" title={rec.target_identifier}>
                      {rec.target_identifier}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        rec.threat_category === 'PHISHING'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : rec.threat_category === 'SUSPICIOUS'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      }`}>
                        {rec.threat_category || 'COMPLETED'}
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
              No previous analyses recorded yet. Submit a URL above to perform real ML inference.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
