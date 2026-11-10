import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertOctagon,
  VideoOff,
  Building2,
  FileWarning,
  AlertTriangle,
  Info,
  Zap,
  RefreshCw,
  PhoneCall,
  UserX
} from 'lucide-react';
import { apiService } from '../services/api';
import type { CommunicationAnalyzeResponse } from '../services/api';

export const DigitalArrestPage: React.FC = () => {
  const [suspectText, setSuspectText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<CommunicationAnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sampleArrestScams = [
    {
      title: 'Fake Mumbai Police / Contraband Parcel',
      text: 'NOTICE FROM MUMBAI POLICE: A FedEx courier with 5 fake passports and 140g MDMA drugs was sent under your Aadhaar. FIR registered. You are in Digital Arrest. Do not disconnect video call.'
    },
    {
      title: 'Fake CBI / Money Laundering Arrest Warrant',
      text: 'CBI Head Office New Delhi: Non-bailable arrest warrant issued against you for 23 crore money laundering. Supreme Court orders digital custody. Transfer security deposit to RBI safe account immediately.'
    },
    {
      title: 'TRAI Mobile Disconnection Threat',
      text: 'TRAI Alert: Your mobile number has been used in 17 illegal harassment activities. Number will be disconnected in 2 hours and local police will arrest you. Press 9 now.'
    }
  ];

  const handleAnalyze = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!suspectText.trim()) {
      setError('Please provide suspect conversation text, caller claims, or message.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    const response = await apiService.analyzeCommunication(suspectText.trim(), true);
    setIsAnalyzing(false);

    if (response.data) {
      setResult(response.data);
    } else {
      setError(response.error || 'Failed to analyze scenario.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* Alert Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-rose-950/40 via-red-900/20 to-black border border-rose-500/30 p-6 sm:p-8 backdrop-blur-md relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40">
                CRITICAL THREAT MITIGATION
              </span>
              <span className="text-xs text-rose-300/80 font-mono">
                CBI / Police Impersonation Countermeasures
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white mt-2 tracking-wide flex items-center gap-2">
              <ShieldAlert className="w-8 h-8 text-rose-400" />
              Digital Arrest Protection Center
            </h1>
            <p className="text-sm text-gray-300 mt-1 max-w-2xl leading-relaxed">
              In India, cyber criminals impersonate law enforcement (CBI, ED, Police, Courts, Customs)
              claiming your Aadhaar is linked to illegal narcotics or money laundering, intimidating victims into
              staying on video calls ("Digital Arrest") and transferring money to fake verification accounts.
            </p>
          </div>

          <div className="bg-black/60 border border-rose-500/40 rounded-xl p-4 min-w-[260px] text-center">
            <span className="text-[10px] uppercase font-mono text-gray-400 tracking-wider">
              Emergency Indian Cybercrime Helpline
            </span>
            <div className="text-3xl font-extrabold font-mono text-[#00F0FF] mt-1 flex items-center justify-center gap-2">
              <PhoneCall className="w-6 h-6 text-rose-400" />
              1930
            </div>
            <span className="text-[11px] text-gray-400 font-mono block mt-1">
              or visit <span className="text-white underline">cybercrime.gov.in</span>
            </span>
          </div>
        </div>
      </div>

      {/* Input Scenario Box */}
      <div className="bg-[#0A1128]/70 border border-[#1E2E5C] rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-4">
        <label className="block text-sm font-medium text-gray-200">
          Enter Call Transcription, WhatsApp Video Claims, or Intimidation Message:
        </label>
        <textarea
          rows={4}
          value={suspectText}
          onChange={(e) => setSuspectText(e.target.value)}
          placeholder="e.g. Someone calling in police uniform claims my Aadhaar card was used to send an illegal parcel to Taiwan containing drugs, and says I am placed under digital arrest unless I transfer 5 lakhs to a clearance account."
          className="w-full p-4 bg-[#050811] border border-[#1E2E5C] focus:border-rose-400 focus:ring-1 focus:ring-rose-400 rounded-xl text-white placeholder-gray-500 font-mono text-sm leading-relaxed"
          disabled={isAnalyzing}
        />

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-gray-400 font-mono">Real-world scam templates:</span>
            {sampleArrestScams.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setSuspectText(s.text)}
                className="text-xs px-2.5 py-1 rounded-lg bg-[#050811] hover:bg-rose-950/40 text-gray-300 border border-gray-800 hover:border-rose-500/40 transition-colors"
              >
                {s.title}
              </button>
            ))}
          </div>

          <button
            onClick={() => handleAnalyze()}
            disabled={isAnalyzing || !suspectText.trim()}
            className="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-rose-500 to-red-700 hover:from-rose-600 hover:to-red-800 text-white font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all shadow-[0_0_15px_rgba(244,63,94,0.3)] disabled:opacity-50"
          >
            {isAnalyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Evaluating Coercion Vectors...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                <span>Analyze Threat Scenario</span>
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

      {/* Analysis Results View */}
      {result && (
        <div className="space-y-6 animate-fadeIn">
          <div className={`rounded-2xl border p-6 sm:p-8 backdrop-blur-md ${
            result.risk_level === 'CRITICAL' || result.risk_level === 'HIGH'
              ? 'bg-rose-950/20 border-rose-500/40 text-rose-300'
              : 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
          }`}>
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 border-b border-gray-700/40">
              <div className="flex items-start space-x-4">
                <div className="p-3 rounded-xl bg-black/40 border border-white/10 shadow-inner">
                  {result.risk_level === 'CRITICAL' ? (
                    <AlertOctagon className="w-9 h-9 text-rose-400 animate-pulse" />
                  ) : (
                    <ShieldCheck className="w-9 h-9 text-emerald-400" />
                  )}
                </div>
                <div>
                  <div className="flex items-center space-x-3">
                    <span className="text-xs uppercase tracking-widest font-mono font-bold px-2 py-0.5 rounded bg-black/40 border border-white/10">
                      {result.classification.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs font-mono text-gray-300">
                      Coercion Confidence: {(result.confidence ? (result.confidence * 100).toFixed(1) : '99.0')}%
                    </span>
                  </div>
                  <h2 className="text-xl sm:text-2xl font-bold text-white mt-1.5">
                    {result.risk_level === 'CRITICAL'
                      ? 'Confirmed Digital Arrest Scam Modus Operandi'
                      : 'No Digital Arrest Signatures Found'}
                  </h2>
                </div>
              </div>

              <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-black/40 border border-white/10 min-w-[160px]">
                <span className="text-xs font-mono text-gray-300">THREAT SCORE</span>
                <div className="text-3xl sm:text-4xl font-extrabold font-mono mt-1 text-white">
                  {result.risk_score.toFixed(1)}
                  <span className="text-xs text-gray-400 font-normal"> / 100</span>
                </div>
                <span className={`text-[10px] font-mono uppercase tracking-wider mt-1 px-2 py-0.5 rounded ${
                  result.risk_level === 'CRITICAL' ? 'bg-rose-500 text-black font-bold' : 'bg-emerald-500 text-black font-bold'
                }`}>
                  {result.risk_level} SEVERITY
                </span>
              </div>
            </div>

            {/* Explanation */}
            <div className="mt-6 p-4 rounded-xl bg-black/30 border border-white/5 flex items-start space-x-3">
              <Info className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-xs font-mono text-rose-400 uppercase font-semibold">
                  Why this scenario was classified this way:
                </div>
                <p className="text-sm text-gray-200 mt-1 leading-relaxed">
                  {result.explanation}
                </p>
              </div>
            </div>

            {/* Action Playbook */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
              <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                <h3 className="text-xs font-mono uppercase text-gray-300 font-semibold mb-3 flex items-center gap-1.5">
                  <FileWarning className="w-4 h-4 text-amber-400" />
                  Identified Scam Elements
                </h3>
                <ul className="space-y-2">
                  {result.detected_indicators.map((ind, i) => (
                    <li key={i} className="text-xs text-rose-300 flex items-start space-x-2">
                      <span className="text-rose-500 font-bold">•</span>
                      <span>{ind}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-black/20 border border-white/5">
                <h3 className="text-xs font-mono uppercase text-gray-300 font-semibold mb-3 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Immediate Protection Protocol
                </h3>
                <ul className="space-y-2">
                  {result.recommendations.map((rec, i) => (
                    <li key={i} className="text-xs text-gray-200 flex items-start space-x-2">
                      <span className="text-emerald-400 font-bold">✓</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Facts & Guidelines */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-5 rounded-2xl bg-[#0A1128]/70 border border-[#1E2E5C] space-y-2">
          <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
            <VideoOff className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-white">No Video-Call Custody</h3>
          <p className="text-xs text-gray-400 leading-relaxed">
            Indian Law does not recognize 'Digital Arrest'. Genuine police officers and CBI investigators
            never arrest people or conduct interrogations over Skype, WhatsApp, or video calls.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-[#0A1128]/70 border border-[#1E2E5C] space-y-2">
          <div className="w-10 h-10 rounded-xl bg-[#00F0FF]/10 border border-[#00F0FF]/30 flex items-center justify-center text-[#00F0FF]">
            <Building2 className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-white">No 'Safe' Accounts</h3>
          <p className="text-xs text-gray-400 leading-relaxed">
            There is no concept of a 'Secret RBI Account' or 'Government Verification Account'. Any caller
            asking you to transfer funds to verify innocence is a criminal.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-[#0A1128]/70 border border-[#1E2E5C] space-y-2">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <UserX className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-white">Break the Isolation</h3>
          <p className="text-xs text-gray-400 leading-relaxed">
            Scammers demand secrecy to prevent family intervention. Immediately disconnect the call,
            speak to trusted relatives, and report the phone number to 1930.
          </p>
        </div>
      </div>
    </div>
  );
};
