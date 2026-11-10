import React, { useState } from 'react';
import {
  CheckCircle2,
  Clock,
  Code,
  Terminal,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import type { SystemInfoData, HealthCheckData } from '../services/api';

interface SystemInfoPageProps {
  systemInfo: SystemInfoData | null;
  health: HealthCheckData | null;
  isOnline: boolean;
}

export const SystemInfoPage: React.FC<SystemInfoPageProps> = ({
  systemInfo,
  health,
  isOnline,
}) => {
  const [showRawJson, setShowRawJson] = useState(false);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Title */}
      <div className="border-b border-[#1E2E5C] pb-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
                System Diagnostics & Architecture
              </h1>
              <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold bg-[#00F0FF]/15 text-[#00F0FF] border border-[#00F0FF]/30">
                Live Backend Spec
              </span>
            </div>
            <p className="text-gray-400 text-xs sm:text-sm mt-1">
              Verified component state, database engine parameters, and runtime environment.
            </p>
          </div>

          <button
            onClick={() => setShowRawJson(!showRawJson)}
            className="px-3 py-1.5 rounded-lg text-xs font-mono bg-slate-900 border border-slate-700 text-gray-300 hover:text-white flex items-center space-x-1.5 cursor-pointer"
          >
            <Code className="w-3.5 h-3.5 text-[#00F0FF]" />
            <span>{showRawJson ? 'Hide Raw JSON' : 'Inspect Raw JSON'}</span>
            {showRawJson ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
        </div>
      </div>

      {/* Raw JSON Accordion if toggled */}
      {showRawJson && (
        <div className="p-4 rounded-xl bg-black/80 border border-cyan-500/30 font-mono text-xs text-cyan-300 overflow-x-auto shadow-2xl">
          <div className="text-[11px] text-gray-400 mb-2 font-bold flex items-center justify-between">
            <span>GET /api/system/info Payload</span>
            <span className="text-emerald-400">Status 200 OK</span>
          </div>
          <pre>{JSON.stringify(systemInfo, null, 2)}</pre>
        </div>
      )}

      {/* Overview Metadata Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="cyber-card p-5 rounded-xl space-y-2">
          <div className="text-xs font-mono text-gray-400 uppercase">Application</div>
          <div className="text-lg font-bold text-white">
            {systemInfo?.application_name || 'Cyber Raksha AI'}
          </div>
          <div className="text-xs text-gray-400 font-mono">
            Version: {systemInfo?.version || '1.0.0'}
          </div>
        </div>

        <div className="cyber-card p-5 rounded-xl space-y-2">
          <div className="text-xs font-mono text-gray-400 uppercase">API Status</div>
          <div className="flex items-center space-x-2">
            <span className={`pulse-indicator ${isOnline ? 'bg-emerald-400' : 'bg-rose-400'}`} />
            <span className={`text-lg font-bold font-mono ${isOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
              {isOnline ? 'OPERATIONAL' : 'OFFLINE'}
            </span>
          </div>
          <div className="text-xs text-gray-400 font-mono">
            Environment: {systemInfo?.environment || 'development'}
          </div>
          <div className="text-[11px] text-gray-500 font-mono">
            Uptime: {health?.uptime_seconds ? `${health.uptime_seconds}s` : 'N/A'}
          </div>
        </div>

        <div className="cyber-card p-5 rounded-xl space-y-2">
          <div className="text-xs font-mono text-gray-400 uppercase">Database Dialect</div>
          <div className="text-lg font-bold text-cyan-400 font-mono">
            {systemInfo?.database_status?.dialect.toUpperCase() || 'SQLITE'}
          </div>
          <div className="text-xs text-gray-400">
            {systemInfo?.database_status?.storage || 'Local Relational Database'}
          </div>
        </div>

        <div className="cyber-card p-5 rounded-xl space-y-2">
          <div className="text-xs font-mono text-gray-400 uppercase">Development Stage</div>
          <div className="text-lg font-bold text-white font-mono">
            Stage 1
          </div>
          <div className="text-xs text-blue-300">
            {systemInfo?.development_stage || 'Complete Project Foundation'}
          </div>
        </div>
      </div>

      {/* Implemented vs Planned Components Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Implemented in Stage 1 */}
        <div className="p-6 rounded-xl bg-[#0B132B]/50 border border-[#1E2E5C] space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h3 className="font-bold text-white text-base">
                Implemented Components (Stage 1)
              </h3>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              {systemInfo?.implemented_components?.length || 0} Delivered
            </span>
          </div>

          <p className="text-xs text-gray-400">
            The following architectural foundation components are fully implemented, verified, and operational:
          </p>

          <ul className="space-y-2.5 text-xs">
            {(systemInfo?.implemented_components || [
              'FastAPI REST API Core Engine & CORS Middleware',
              'Pydantic V2 Validation Layer',
              'SQLAlchemy 2.0 ORM Architecture',
              'SQLite Relational Persistence',
              '5 Core Database Schemas',
              'Real-time Active Database Health Ping',
              'React 19 + TypeScript + Vite Frontend',
              'Tailwind CSS Dark Cybersecurity Theme',
              'Three.js 3D Wireframe Architecture',
              'Centralized API Service with Fallbacks',
              'Pytest Test Suite Verification'
            ]).map((comp, idx) => (
              <li key={idx} className="flex items-start space-x-2.5 p-2 rounded-lg bg-slate-900/40 border border-slate-800/80">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span className="text-gray-300 font-medium">{comp}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Planned for Future Stages */}
        <div className="p-6 rounded-xl bg-[#0B132B]/50 border border-[#1E2E5C] space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5 text-amber-400" />
              <h3 className="font-bold text-white text-base">
                Planned Components (Future Stages)
              </h3>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30">
              {systemInfo?.planned_components?.length || 0} Planned
            </span>
          </div>

          <p className="text-xs text-gray-400">
            Machine learning models and advanced intelligence pipelines scheduled for subsequent stages:
          </p>

          <ul className="space-y-2.5 text-xs">
            {(systemInfo?.planned_components || [
              'AI-Powered Phishing Detection Model & Tokenizer (Stage 2)',
              'Malicious URL & Heuristic Domain Classifier (Stage 2)',
              'Voice Cloning & Audio Deepfake Spectral Analyzer (Stage 3)',
              'Multimodal Suspicious Communication Risk Analyzer (Stage 3)',
              'Threat Intelligence Feed Aggregator & CVE Matcher (Stage 4)',
              'Multi-Layer Fraud-Risk Assessment Scoring Engine (Stage 4)',
              'Explainable AI (XAI) Feature Importance Engine (Stage 5)',
              'Android Client & Cross-Platform Shell (Stage 5)'
            ]).map((comp, idx) => (
              <li key={idx} className="flex items-start space-x-2.5 p-2 rounded-lg bg-slate-900/40 border border-slate-800/80">
                <Clock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <span className="text-gray-300">{comp}</span>
              </li>
            ))}
          </ul>
        </div>

      </div>

      {/* Technology Architecture Matrix */}
      <div className="p-6 rounded-xl bg-[#0B132B]/30 border border-[#1E2E5C] space-y-4">
        <h3 className="font-bold text-white text-sm flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-[#00F0FF]" />
          <span>Technology Architecture Matrix</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="font-bold text-cyan-300 block">Frontend Stack</span>
            <ul className="space-y-1 text-gray-400">
              <li>• React 19 + TypeScript 5.8</li>
              <li>• Vite Build Pipeline</li>
              <li>• Tailwind CSS (Dark Cyber Aesthetic)</li>
              <li>• Three.js 3D Telemetry Canvas</li>
              <li>• Lucide React Icons</li>
            </ul>
          </div>

          <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="font-bold text-cyan-300 block">Backend Stack</span>
            <ul className="space-y-1 text-gray-400">
              <li>• FastAPI (Python 3.13)</li>
              <li>• Uvicorn High-Performance ASGI</li>
              <li>• Pydantic V2 Schemas</li>
              <li>• CORS Policy Controls</li>
              <li>• Pytest Automated Suite</li>
            </ul>
          </div>

          <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="font-bold text-cyan-300 block">Data & AI Subsystem</span>
            <ul className="space-y-1 text-gray-400">
              <li>• SQLite (Local Relational Engine)</li>
              <li>• SQLAlchemy 2.0 ORM</li>
              <li>• PostgreSQL Migration Architecture</li>
              <li>• Modular AI Engine Directory</li>
              <li>• Zero Paid API Dependency</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
