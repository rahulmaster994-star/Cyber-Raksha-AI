import React from 'react';
import { Shield, Terminal, BookOpen, Lock } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full border-t border-[#1E2E5C]/60 bg-[#050811] py-8 text-gray-400 text-xs mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-[#00F0FF]" />
            <span className="font-semibold text-gray-200">CYBER RAKSHA AI</span>
            <span className="text-gray-500">|</span>
            <span className="font-mono text-cyan-400">Stage 1: Complete Project Foundation</span>
          </div>

          <div className="flex items-center space-x-6">
            <a
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1.5 text-gray-300 hover:text-[#00F0FF] transition-colors"
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Swagger OpenAPI</span>
            </a>
            <a
              href="http://127.0.0.1:8000/redoc"
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1.5 text-gray-300 hover:text-[#00F0FF] transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>ReDoc Specs</span>
            </a>
            <div className="flex items-center space-x-1 text-emerald-400">
              <Lock className="w-3.5 h-3.5" />
              <span>FOSS Core</span>
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-900/80 text-center md:text-left text-[11px] text-gray-500 flex flex-col md:flex-row justify-between items-center gap-2">
          <p>
            Architectural Foundation: Open-source, zero paid APIs, zero proprietary locks. Security detection modules are in planned standby status.
          </p>
          <p className="font-mono text-slate-500">
            PostgreSQL-ready • SQLite 3.x • FastAPI ASGI • React 19
          </p>
        </div>
      </div>
    </footer>
  );
};
