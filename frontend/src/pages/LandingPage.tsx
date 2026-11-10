import React from 'react';
import { Shield, Cpu, Lock, ArrowRight, CheckCircle2, AlertTriangle, Activity } from 'lucide-react';
import { ThreeCyberOrb } from '../components/ThreeCyberOrb';

interface LandingPageProps {
  onGetStarted: () => void;
  onExploreModules: () => void;
  isBackendOnline: boolean;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onGetStarted,
  onExploreModules,
  isBackendOnline,
}) => {
  return (
    <div className="relative overflow-hidden py-10 lg:py-16">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Hero Left Content */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-[#00F0FF]/10 border border-[#00F0FF]/30 text-[#00F0FF] text-xs font-mono font-medium">
              <span className="pulse-indicator bg-[#00F0FF]" />
              <span>STAGE 10: RELEASE CANDIDATE (v1.0.0-rc.1)</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-tight">
              Defend Against Modern Cyber Threats with{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00F0FF] via-[#38BDF8] to-[#0070F3] cyber-glow-text">
                CYBER RAKSHA AI
              </span>
            </h1>

            <p className="text-lg text-gray-300 leading-relaxed">
              An intelligent, verified cybersecurity platform engineered to detect, analyse, explain, and prevent digital threats using artificial intelligence, machine learning, and real-time threat intelligence.
            </p>

            {/* Stage 10 Real Status Banner */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-[#1E2E5C] flex items-start space-x-3">
              <div className="p-2 rounded-lg bg-[#00F0FF]/10 text-[#00F0FF] shrink-0 mt-0.5">
                <Activity className="w-5 h-5" />
              </div>
              <div className="text-sm">
                <div className="font-semibold text-white flex items-center space-x-2">
                  <span>Current Stage: Production Release Candidate (v1.0.0-rc.1)</span>
                  <span className={`text-[11px] px-2 py-0.5 rounded ${isBackendOnline ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'}`}>
                    {isBackendOnline ? 'Backend Online' : 'Backend Disconnected'}
                  </span>
                </div>
                <p className="text-gray-400 text-xs mt-1">
                  All 10 development stages complete: Supervised ML phishing classifier, communication fraud NLP, voice clone detection, real-time URLhaus threat intelligence, proactive prevention playbooks, Manifest V3 Chromium extension, Android/PWA companion, and system observability.
                </p>
              </div>
            </div>

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                id="cta-get-started"
                onClick={onGetStarted}
                className="px-6 py-3 rounded-lg font-semibold text-sm bg-gradient-to-r from-[#00F0FF] to-[#0070F3] text-black hover:opacity-95 shadow-[0_0_25px_rgba(0,240,255,0.35)] transition-all flex items-center space-x-2 cursor-pointer"
              >
                <span>Enter Control Center</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                id="cta-explore-modules"
                onClick={onExploreModules}
                className="px-6 py-3 rounded-lg font-semibold text-sm bg-[#0B132B]/80 text-gray-200 border border-[#1E2E5C] hover:border-[#00F0FF]/50 hover:text-white transition-all flex items-center space-x-2 cursor-pointer"
              >
                <Cpu className="w-4 h-4 text-[#00F0FF]" />
                <span>View Security Modules</span>
              </button>
            </div>
          </div>

          {/* Hero Right Visual: Three.js 3D Cyber Visualization */}
          <div className="lg:col-span-5 relative flex items-center justify-center">
            <div className="w-full max-w-[460px] h-[420px] rounded-2xl bg-gradient-to-b from-[#0B132B]/80 to-[#050811]/90 border border-[#1E2E5C] p-4 flex flex-col items-center justify-center shadow-[0_0_40px_rgba(0,112,243,0.15)] relative overflow-hidden">
              <div className="absolute top-3 left-4 flex items-center space-x-2 z-10">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-mono text-cyan-400">TELEMETRY_3D_SUB_NODE</span>
              </div>
              
              {/* Three.js Orb */}
              <ThreeCyberOrb className="w-full h-full" />

              <div className="absolute bottom-3 inset-x-4 flex justify-between items-center text-[11px] font-mono text-gray-400 border-t border-slate-800/80 pt-2 z-10">
                <span>CANVAS: WebGL Active</span>
                <span>STAGE: Wireframe Architecture</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Purpose & Objectives Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-20">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <h2 className="text-xs uppercase tracking-widest text-[#00F0FF] font-mono font-bold">
            Project Objectives
          </h2>
          <p className="text-3xl font-bold text-white">
            Architected to Neutralize Multi-Vector Digital Attacks
          </p>
          <p className="text-gray-400 text-sm">
            Cyber Raksha AI addresses the escalating threat landscape where attacks transcend conventional perimeter firewalls through social engineering, acoustic cloning, and deceptive communication.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          {/* Card 1 */}
          <div className="cyber-card p-6 rounded-xl space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-[#00F0FF]">
              <Shield className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-white">1. Detect & Analyze</h3>
            <p className="text-gray-400 text-xs leading-relaxed">
              Synthesizes real-time signals across text, URLs, voice patterns, and multi-channel messaging to detect sophisticated deception vectors.
            </p>
          </div>

          {/* Card 2 */}
          <div className="cyber-card p-6 rounded-xl space-y-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-[#00F0FF]">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-white">2. Explainable AI</h3>
            <p className="text-gray-400 text-xs leading-relaxed">
              Demystifies threat classifications by providing clear explanations and evidence traces instead of opaque black-box verdict scores.
            </p>
          </div>

          {/* Card 3 */}
          <div className="cyber-card p-6 rounded-xl space-y-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-[#38BDF8]">
              <Lock className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-white">3. Help Prevent</h3>
            <p className="text-gray-400 text-xs leading-relaxed">
              Delivers automated prevention playbooks, risk mitigation advice, and continuous security posture recommendations for individuals and enterprises.
            </p>
          </div>
        </div>
      </div>

      {/* Roadmap & Feature Overview */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-20">
        <div className="p-8 rounded-2xl bg-[#0B132B]/40 border border-[#1E2E5C]">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
            <div>
              <h3 className="text-xl font-bold text-white">Capability Roadmap & Development Stages</h3>
              <p className="text-xs text-gray-400 mt-1">
                Full transparency: Stage 1 delivers the operational foundation. AI models will be integrated in subsequent stages.
              </p>
            </div>
            <span className="text-xs font-mono px-3 py-1 rounded bg-[#00F0FF]/15 text-[#00F0FF] border border-[#00F0FF]/30">
              Stage 1 of 5
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/90 border border-cyan-500/50 shadow-[0_0_15px_rgba(0,240,255,0.1)]">
              <div className="text-[10px] font-mono text-cyan-400 font-bold uppercase">Stage 1 (Current)</div>
              <div className="text-sm font-bold text-white mt-1">Foundation</div>
              <p className="text-[11px] text-gray-400 mt-1">
                FastAPI, SQLite/SQLAlchemy, React 19, Three.js, health diagnostics.
              </p>
              <div className="mt-3 text-[10px] text-emerald-400 flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Implemented</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
              <div className="text-[10px] font-mono text-gray-400 uppercase">Stage 2</div>
              <div className="text-sm font-bold text-gray-300 mt-1">Phishing & URL AI</div>
              <p className="text-[11px] text-gray-500 mt-1">
                NLP email classifiers and lexical URL maliciousness models.
              </p>
              <div className="mt-3 text-[10px] text-amber-400 flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Planned</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
              <div className="text-[10px] font-mono text-gray-400 uppercase">Stage 3</div>
              <div className="text-sm font-bold text-gray-300 mt-1">Audio & Social Eng</div>
              <p className="text-[11px] text-gray-500 mt-1">
                Voice cloning acoustic detector & communication risk analysis.
              </p>
              <div className="mt-3 text-[10px] text-amber-400 flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Planned</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
              <div className="text-[10px] font-mono text-gray-400 uppercase">Stage 4</div>
              <div className="text-sm font-bold text-gray-300 mt-1">Threat Intel & Fraud</div>
              <p className="text-[11px] text-gray-500 mt-1">
                OSINT IoC integration and multi-layer fraud scoring.
              </p>
              <div className="mt-3 text-[10px] text-amber-400 flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Planned</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
              <div className="text-[10px] font-mono text-gray-400 uppercase">Stage 5</div>
              <div className="text-sm font-bold text-gray-300 mt-1">XAI & Mobile Client</div>
              <p className="text-[11px] text-gray-500 mt-1">
                Explainable AI engine & Android mobile application.
              </p>
              <div className="mt-3 text-[10px] text-amber-400 flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Planned</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
