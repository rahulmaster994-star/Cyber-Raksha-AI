import React from 'react';
import {
  Mail,
  Globe,
  Mic,
  MessageSquare,
  Shield,
  Sliders,
  AlertTriangle,
  HelpCircle,
  Clock
} from 'lucide-react';
import type { SecurityModulesResponse } from '../services/api';

interface SecurityModulesPageProps {
  modulesData: SecurityModulesResponse | null;
  isLoading: boolean;
}

// Icon mapping helper
const getModuleIcon = (code: string) => {
  switch (code) {
    case 'PHISH_DETECT':
      return <Mail className="w-6 h-6 text-[#00F0FF]" />;
    case 'URL_DETECT':
      return <Globe className="w-6 h-6 text-[#38BDF8]" />;
    case 'VOICE_DETECT':
      return <Mic className="w-6 h-6 text-purple-400" />;
    case 'COMM_RISK':
      return <MessageSquare className="w-6 h-6 text-indigo-400" />;
    case 'THREAT_INTEL':
      return <Shield className="w-6 h-6 text-cyan-300" />;
    case 'RISK_ASSESS':
      return <Sliders className="w-6 h-6 text-blue-400" />;
    default:
      return <Shield className="w-6 h-6 text-[#00F0FF]" />;
  }
};

export const SecurityModulesPage: React.FC<SecurityModulesPageProps> = ({
  modulesData,
  isLoading,
}) => {
  const modules = modulesData?.modules || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Title */}
      <div className="border-b border-[#1E2E5C] pb-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
                Security Modules Catalog
              </h1>
              <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                Stage 1: Architecture Only
              </span>
            </div>
            <p className="text-gray-400 text-xs sm:text-sm mt-1">
              Architectural definitions for the six core Cyber Raksha AI detection engines.
            </p>
          </div>

          <div className="flex items-center space-x-3 text-xs font-mono">
            <span className="px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-300 border border-amber-500/30 flex items-center space-x-1.5">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>All 6 Modules: PLANNED / NOT IMPLEMENTED</span>
            </span>
          </div>
        </div>
      </div>

      {/* Transparency Banner */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-[#1E2E5C] text-xs text-gray-300 flex items-start space-x-3">
        <HelpCircle className="w-5 h-5 text-[#00F0FF] shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-white text-sm block">
            Stage 1 Implementation Notice
          </span>
          <p className="mt-1 text-gray-400 leading-relaxed">
            Per the Stage 1 specification, no detection models, synthetic detection statistics, or simulated threat telemetry are generated. The modules below present verified future capabilities that will be implemented across Stages 2 through 5.
          </p>
        </div>
      </div>

      {/* Six Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {modules.map((module) => (
          <div
            key={module.id}
            className="cyber-card p-6 rounded-xl flex flex-col justify-between space-y-4 relative overflow-hidden"
          >
            {/* Top Row: Icon, Name & Status Badge */}
            <div>
              <div className="flex justify-between items-start mb-3">
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-700/60 shadow-inner">
                  {getModuleIcon(module.code)}
                </div>

                <div className="flex flex-col items-end space-y-1">
                  <span className="text-[10px] px-2.5 py-1 rounded font-mono font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                    PLANNED / NOT IMPLEMENTED
                  </span>
                  <span className="text-[10px] text-gray-400 font-mono">
                    Target: {module.stage_planned}
                  </span>
                </div>
              </div>

              <div className="text-xs font-mono text-cyan-400 tracking-wider">
                {module.category}
              </div>
              <h2 className="text-lg font-bold text-white mt-1">
                {module.name}
              </h2>
              <p className="text-gray-400 text-xs mt-2 leading-relaxed">
                {module.description}
              </p>
            </div>

            {/* Planned Capabilities */}
            <div className="pt-4 border-t border-slate-800/80 space-y-2">
              <div className="text-[11px] font-semibold text-gray-300 flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                <span>Planned AI Capabilities:</span>
              </div>
              <ul className="space-y-1.5 text-[11px] text-gray-400">
                {module.planned_capabilities.map((cap, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-cyan-400 mt-0.5">•</span>
                    <span>{cap}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Stage Indicator Bar */}
            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-gray-400">
              <span>Code: {module.code}</span>
              <span className="text-amber-400/90 flex items-center space-x-1">
                <AlertTriangle className="w-3 h-3" />
                <span>Model Standby</span>
              </span>
            </div>
          </div>
        ))}
      </div>

      {isLoading && (
        <div className="text-center py-12 text-gray-400 font-mono text-xs">
          Loading Security Modules Registry from FastAPI backend...
        </div>
      )}
    </div>
  );
};
