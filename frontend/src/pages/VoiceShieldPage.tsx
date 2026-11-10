import React, { useState, useEffect, useRef } from 'react';
import { apiService } from '../services/api';
import type {
  AudioAnalysisResponse,
  AudioStatusResponse,
  AnalysisHistoryItem,
} from '../services/api';

export const VoiceShieldPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AudioAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<AudioStatusResponse | null>(null);
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadTelemetry();
    loadHistory();
  }, []);

  const loadTelemetry = async () => {
    const res = await apiService.getAudioStatus();
    if (res.data) setStatus(res.data);
  };

  const loadHistory = async () => {
    const res = await apiService.getAudioHistory(10);
    if (res.data) setHistory(res.data.records);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.toLowerCase().endsWith('.wav')) {
        setError('Only .wav audio files are supported currently.');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setError(null);
      setResult(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (!file.name.toLowerCase().endsWith('.wav')) {
        setError('Only .wav audio files are supported currently.');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setError(null);
      setResult(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError('Please select or upload a WAV audio file first.');
      return;
    }
    setAnalyzing(true);
    setError(null);

    const res = await apiService.analyzeAudio(selectedFile);
    setAnalyzing(false);

    if (res.error) {
      setError(res.error);
    } else if (res.data) {
      setResult(res.data);
      loadHistory();
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
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium tracking-wide bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                STAGE 4 INTELLIGENCE
              </span>
              <span className="text-xs font-mono text-gray-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                ACOUSTIC ENGINE ONLINE
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold font-mono tracking-tight text-white mt-2">
              Voice Shield — AI Deepfake Audio Detection
            </h1>
            <p className="text-gray-400 text-sm mt-1 max-w-2xl">
              Inspect suspicious phone recordings, voice notes, and audio messages for neural speech synthesis, 
              TTS vocoder artifacts, and telephonic voice cloning.
            </p>
          </div>
          {status && (
            <div className="flex flex-wrap md:flex-col items-start md:items-end gap-2 text-xs font-mono bg-cyber-bg/50 p-3 rounded-lg border border-gray-800">
              <div className="text-gray-400">
                MODEL: <span className="text-cyan-400">{status.model_name}</span>
              </div>
              <div className="text-gray-400">
                ACCURACY: <span className="text-emerald-400">{status.accuracy ? `${(status.accuracy * 100).toFixed(1)}%` : 'Active'}</span>
              </div>
              <div className="text-gray-400">
                FEATURES: <span className="text-purple-400">{status.features_count} Acoustic MFCC/Spectral</span>
              </div>
            </div>
          )}
        </div>

        {/* Forensic Capability & Non-Biometric Scope Disclaimer */}
        <div className="mt-4 pt-3 border-t border-cyan-500/20 flex items-start gap-2.5 text-xs text-gray-300">
          <svg className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="leading-relaxed">
            <strong className="text-cyan-300 font-mono font-medium">Forensic Scope:</strong> This engine evaluates acoustic and vocoder signal anomalies (zero-crossing rate, spectral flatness, phase shifts) to detect generative AI voice synthesis. It <strong className="text-white">DOES NOT authenticate speaker biometric identity</strong> or prove legal identity.
          </p>
        </div>
      </div>

      {/* Main Analysis Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload & Inspect Column */}
        <div className="lg:col-span-2 space-y-6">
          <div className="border border-gray-800 bg-cyber-card/40 rounded-xl p-6 backdrop-blur-sm">
            <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z" />
              </svg>
              Upload Audio Sample for Forensic Inspection
            </h2>

            {/* Drop Zone */}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                selectedFile
                  ? 'border-cyan-500 bg-cyan-950/20'
                  : 'border-gray-700 hover:border-cyan-500/60 bg-cyber-bg/40 hover:bg-cyber-bg/70'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".wav"
                onChange={handleFileChange}
                className="hidden"
              />
              <div className="mx-auto w-12 h-12 mb-3 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>

              {selectedFile ? (
                <div>
                  <p className="text-white font-medium font-mono text-sm">{selectedFile.name}</p>
                  <p className="text-gray-400 text-xs mt-1">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready for inference
                  </p>
                  <p className="text-cyan-400 text-xs mt-2 underline">Click to change file</p>
                </div>
              ) : (
                <div>
                  <p className="text-gray-200 font-medium text-sm">Drag & drop a WAV recording here, or browse</p>
                  <p className="text-gray-500 text-xs mt-1">Accepts standard .wav audio files (max 25MB, up to 5 mins)</p>
                </div>
              )}
            </div>

            {error && (
              <div className="mt-4 p-3 rounded-lg bg-red-950/30 border border-red-500/40 text-red-300 text-xs flex items-center gap-2">
                <svg className="w-4 h-4 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {error}
              </div>
            )}

            <div className="mt-6 flex items-center justify-between">
              <span className="text-xs text-gray-500 font-mono">
                PRIVACY: Audio is analyzed strictly in-memory. Never retained on disk.
              </span>
              <button
                onClick={handleAnalyze}
                disabled={!selectedFile || analyzing}
                className={`px-5 py-2.5 rounded-lg font-mono text-sm font-semibold tracking-wide transition-all shadow-lg ${
                  !selectedFile || analyzing
                    ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black shadow-cyan-500/20'
                }`}
              >
                {analyzing ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                    Extracting Acoustic Features...
                  </span>
                ) : (
                  'Analyze Voice Recording'
                )}
              </button>
            </div>
          </div>

          {/* Results Panel */}
          {result && (
            <div className="border border-gray-800 bg-cyber-card/60 rounded-xl p-6 backdrop-blur-md space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-800">
                <div>
                  <span className="text-xs font-mono text-gray-400 uppercase tracking-wider">Classification Verdict</span>
                  <div className="flex items-center gap-3 mt-1">
                    <span className={`px-3 py-1 rounded-md font-mono text-sm font-bold border ${getRiskColor(result.risk_level)}`}>
                      {result.classification.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs text-gray-400 font-mono">
                      Risk Level: <strong className="text-white">{result.risk_level}</strong>
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4 bg-cyber-bg/70 px-4 py-2.5 rounded-xl border border-gray-800">
                  <div className="text-right">
                    <div className="text-xs text-gray-400 font-mono">THREAT SCORE</div>
                    <div className="text-2xl font-mono font-bold text-white">{result.risk_score}<span className="text-xs text-gray-500">/100</span></div>
                  </div>
                  <div className="w-12 h-12 rounded-full border-2 border-cyan-500/40 flex items-center justify-center font-mono text-xs text-cyan-300">
                    {result.risk_score}%
                  </div>
                </div>
              </div>

              {/* Explanation Text */}
              <div className="p-4 rounded-lg bg-cyber-bg/40 border border-gray-800 text-sm text-gray-300 leading-relaxed">
                <h4 className="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1">Acoustic Assessment</h4>
                <p>{result.explanation}</p>
              </div>

              {/* Detected Forensic Indicators */}
              <div>
                <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400 mb-3">
                  Detected Acoustic Indicators ({result.detected_indicators.length})
                </h3>
                {result.detected_indicators.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {result.detected_indicators.map((ind, i) => (
                      <div key={i} className="p-3 rounded-lg bg-cyber-bg/40 border border-gray-800/80 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono font-bold text-white">{ind.name}</span>
                          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                            ind.severity === 'HIGH' ? 'text-red-400 border-red-500/40' : 'text-amber-400 border-amber-500/40'
                          }`}>
                            {ind.severity}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 leading-normal">{ind.description}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 text-xs">
                    No anomalous vocoder or speech synthesis artifacts detected in this audio sample.
                  </div>
                )}
              </div>

              {/* Recommendations */}
              <div>
                <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400 mb-2">Safety Recommendations</h3>
                <ul className="space-y-1.5">
                  {result.recommendations.map((rec, i) => (
                    <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                      <span className="text-cyan-400 font-bold">›</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Telemetry & History Sidebar */}
        <div className="space-y-6">
          {/* Quick Guidance Card */}
          <div className="border border-gray-800 bg-cyber-card/40 rounded-xl p-5 backdrop-blur-sm space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-semibold">
              Voice Cloning Threats
            </h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Cybercriminals use modern generative voice cloning to replicate relatives, executives, or law enforcement
              officers with as little as 3 seconds of reference audio.
            </p>
            <div className="space-y-2 text-xs text-gray-300">
              <div className="p-2 rounded bg-cyber-bg/60 border border-gray-800">
                <strong className="text-white block mb-0.5">CEO / Executive Fraud:</strong>
                Urgent requests for wire transfers or gift cards over the phone.
              </div>
              <div className="p-2 rounded bg-cyber-bg/60 border border-gray-800">
                <strong className="text-white block mb-0.5">Family Emergency Scams:</strong>
                Distressed cries for bail or hospital funds from unknown numbers.
              </div>
            </div>
          </div>

          {/* Analysis History */}
          <div className="border border-gray-800 bg-cyber-card/40 rounded-xl p-5 backdrop-blur-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400 font-semibold">
                Recent Voice Analyses
              </h3>
              <span className="text-[10px] font-mono text-cyan-400">{history.length} logged</span>
            </div>

            {history.length > 0 ? (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {history.map((item) => (
                  <div key={item.id} className="p-2.5 rounded-lg bg-cyber-bg/60 border border-gray-800/80 text-xs space-y-1">
                    <div className="flex items-center justify-between font-mono">
                      <span className="text-white truncate max-w-[140px]">{item.target_identifier}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        (item.threat_category || '').includes('VOICE') || (item.threat_category || '').includes('AI')
                          ? 'text-red-400 bg-red-950/30'
                          : 'text-emerald-400 bg-emerald-950/30'
                      }`}>
                        {item.threat_category || 'ANALYSIS'}
                      </span>
                    </div>
                    <div className="text-[10px] text-gray-500 font-mono flex items-center justify-between">
                      <span>Score: {item.risk_score}</span>
                      <span>{new Date(item.created_at).toLocaleTimeString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-500 text-center py-4">No recent audio records.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
