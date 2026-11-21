import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from './layouts/Navbar';
import { Footer } from './layouts/Footer';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { SecurityModulesPage } from './pages/SecurityModulesPage';
import { SystemInfoPage } from './pages/SystemInfoPage';
import { PhishingDetectionPage } from './pages/PhishingDetectionPage';
import { CommunicationThreatPage } from './pages/CommunicationThreatPage';
import { DigitalArrestPage } from './pages/DigitalArrestPage';
import { VoiceShieldPage } from './pages/VoiceShieldPage';
import { ThreatIntelPage } from './pages/ThreatIntelPage';
import { UnifiedThreatAnalyzerPage } from './pages/UnifiedThreatAnalyzerPage';
import { PersonalProtectionPage } from './pages/PersonalProtectionPage';
import { AdminPage } from './pages/AdminPage';
import { apiService } from './services/api';
import type {
  HealthCheckData,
  SystemInfoData,
  SecurityModulesResponse
} from './services/api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'landing' | 'dashboard' | 'phishing' | 'communication' | 'digital-arrest' | 'voice-shield' | 'intel' | 'unified-analyzer' | 'protection-center' | 'modules' | 'system' | 'admin'>(() => {
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get('tab') || params.get('view');
    if (tabParam) return tabParam as any;
    if (window.location.hash) {
      const hashTab = window.location.hash.replace('#', '');
      if (hashTab) return hashTab as any;
    }
    // Default website entry is now the personal Cyber Raksha AI SOC Admin Control Room
    return 'admin';
  });
  const [health, setHealth] = useState<HealthCheckData | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfoData | null>(null);
  const [modulesData, setModulesData] = useState<SecurityModulesResponse | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isLoadingModules, setIsLoadingModules] = useState<boolean>(false);
  const [sharedContent, setSharedContent] = useState<string | null>(null);

  // Fetch full system state from the FastAPI backend
  const fetchState = useCallback(async (isInitial = false) => {
    if (!isInitial) setIsRefreshing(true);

    try {
      // 1. Fetch Health
      const healthRes = await apiService.getHealth();
      if (healthRes.data) {
        setHealth(healthRes.data);
        setIsOnline(true);
        setError(null);
      } else {
        setIsOnline(false);
        setError(healthRes.error);
      }

      // 2. Fetch System Info
      const infoRes = await apiService.getSystemInfo();
      if (infoRes.data) {
        setSystemInfo(infoRes.data);
      }

      // 3. Fetch Modules
      setIsLoadingModules(true);
      const modRes = await apiService.getModules();
      if (modRes.data) {
        setModulesData(modRes.data);
      }
      setIsLoadingModules(false);

    } catch (err: unknown) {
      setIsOnline(false);
      setError(err instanceof Error ? err.message : 'Unknown communication error');
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // Handle URL hash / query routing for direct navigation across modules
  useEffect(() => {
    const syncRoute = () => {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab') || params.get('view');
      if (tabParam) {
        setCurrentTab(tabParam as any);
      } else if (window.location.hash) {
        const hashTab = window.location.hash.replace('#', '');
        if (hashTab) setCurrentTab(hashTab as any);
      } else {
        setCurrentTab('admin');
      }
    };
    window.addEventListener('hashchange', syncRoute);
    window.addEventListener('popstate', syncRoute);
    return () => {
      window.removeEventListener('hashchange', syncRoute);
      window.removeEventListener('popstate', syncRoute);
    };
  }, []);

  // PWA Share Target — handle incoming shared URLs/text from Android share sheet
  // The PWA manifest registers share_target POST to /?title=&text=&url=
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sharedUrl = params.get('url') || params.get('text');
    if (sharedUrl && sharedUrl.trim().length > 0) {
      setSharedContent(sharedUrl.trim());
      setCurrentTab('phishing');
      // Clean the URL bar so the params don't persist on refresh
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  // Initial load and periodic health heartbeat (every 10 seconds)
  useEffect(() => {
    fetchState(true);

    const heartbeatInterval = setInterval(() => {
      // Background heartbeat check
      apiService.getHealth().then((res) => {
        if (res.data) {
          setHealth(res.data);
          setIsOnline(true);
          setError(null);
        } else {
          setIsOnline(false);
          setError(res.error);
        }
      });
    }, 10000);

    return () => clearInterval(heartbeatInterval);
  }, [fetchState]);

  return (
    <div className="min-h-screen bg-[#050811] text-[#F0F6FC] flex flex-col cyber-grid relative selection:bg-[#00F0FF] selection:text-black">
      {/* Top Futuristic Navigation Bar (Hidden in full-screen Admin SOC mode) */}
      {currentTab !== 'admin' && (
        <Navbar
          currentTab={currentTab}
          setCurrentTab={(tab) => setCurrentTab(tab as any)}
          health={health}
          isOnline={isOnline}
          onRefresh={() => fetchState(false)}
          isRefreshing={isRefreshing}
        />
      )}

      {/* Main Dynamic View Content */}
      <main className="flex-1 w-full">
        {currentTab === 'landing' && (
          <LandingPage
            onGetStarted={() => setCurrentTab('phishing')}
            onExploreModules={() => setCurrentTab('modules')}
            isBackendOnline={isOnline}
          />
        )}

        {currentTab === 'dashboard' && (
          <DashboardPage
            health={health}
            systemInfo={systemInfo}
            modulesData={modulesData}
            isOnline={isOnline}
            error={error}
            onRefresh={() => fetchState(false)}
            isRefreshing={isRefreshing}
            onNavigateToModules={() => setCurrentTab('modules')}
            onNavigate={(tab) => setCurrentTab(tab as any)}
          />
        )}

        {currentTab === 'phishing' && (
          <PhishingDetectionPage initialUrl={sharedContent ?? undefined} />
        )}

        {currentTab === 'communication' && (
          <CommunicationThreatPage />
        )}

        {currentTab === 'digital-arrest' && (
          <DigitalArrestPage />
        )}

        {currentTab === 'voice-shield' && (
          <VoiceShieldPage />
        )}

        {currentTab === 'intel' && (
          <ThreatIntelPage />
        )}

        {currentTab === 'unified-analyzer' && (
          <UnifiedThreatAnalyzerPage />
        )}

        {currentTab === 'protection-center' && (
          <PersonalProtectionPage />
        )}

        {currentTab === 'modules' && (
          <SecurityModulesPage
            modulesData={modulesData}
            isLoading={isLoadingModules}
          />
        )}

        {currentTab === 'system' && (
          <SystemInfoPage
            systemInfo={systemInfo}
            health={health}
            isOnline={isOnline}
          />
        )}

        {currentTab === 'admin' && (
          <AdminPage onNavigateToPublic={(tab) => setCurrentTab((tab as any) || 'landing')} />
        )}
      </main>

      {/* Public PWA Mobile Bottom Navigation & Footer (Hidden in full-screen Admin SOC mode) */}
      {currentTab !== 'admin' && (
        <>
          <nav className="fixed bottom-0 left-0 right-0 md:hidden z-50 bg-[#050811]/95 backdrop-blur-md border-t border-[#1E2E5C]/60 flex items-center justify-around px-2 py-2 safe-area-inset-bottom">
            <button
              onClick={() => setCurrentTab('phishing')}
              className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-all ${
                currentTab === 'phishing'
                  ? 'text-[#00F0FF]'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
              aria-label="URL Scan"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span className="text-[9px] font-mono tracking-wide">URL Scan</span>
            </button>
            <button
              onClick={() => setCurrentTab('communication')}
              className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-all ${
                currentTab === 'communication' || currentTab === 'digital-arrest'
                  ? 'text-cyan-400'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
              aria-label="Messages"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <span className="text-[9px] font-mono tracking-wide">Messages</span>
            </button>
            <button
              onClick={() => setCurrentTab('unified-analyzer')}
              className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-all ${
                currentTab === 'unified-analyzer'
                  ? 'text-[#00F0FF]'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
              aria-label="Unified Risk"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span className="text-[9px] font-mono tracking-wide">Unified</span>
            </button>
            <button
              onClick={() => setCurrentTab('protection-center')}
              className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-all ${
                currentTab === 'protection-center'
                  ? 'text-emerald-400'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
              aria-label="Protection"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
              <span className="text-[9px] font-mono tracking-wide">Protect</span>
            </button>
            <button
              onClick={() => setCurrentTab('dashboard')}
              className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-all ${
                currentTab === 'dashboard'
                  ? 'text-[#00F0FF]'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
              aria-label="Dashboard"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span className="text-[9px] font-mono tracking-wide">Control</span>
            </button>
          </nav>

          {/* Bottom padding spacer so content doesn't hide behind mobile nav bar */}
          <div className="md:hidden h-16" aria-hidden="true" />

          {/* Consistent Platform Footer */}
          <Footer onOpenAdmin={() => setCurrentTab('admin')} />
        </>
      )}
    </div>
  );
};

export default App;
