// popup.js — Cyber Raksha AI Chromium Extension Popup Controller
const DEFAULT_API_BASE = 'https://cyberraksha-backend.onrender.com';
const DEFAULT_DASHBOARD_URL = 'https://frontend-lilac-nu-50.vercel.app';

let currentActiveUrl = '';
let apiBaseUrl = DEFAULT_API_BASE;

document.addEventListener('DOMContentLoaded', async () => {
  // Load saved API URL setting if present
  try {
    const stored = await chrome.storage.sync.get(['apiUrl']);
    if (stored.apiUrl) {
      apiBaseUrl = stored.apiUrl.replace(/\/+$/, '');
    }
  } catch (e) {}

  checkBackendStatus();
  fetchCurrentTabUrl();
  loadProtectionTelemetry();

  document.getElementById('btnScanCurrent').addEventListener('click', handleScanCurrent);
  document.getElementById('btnScanManual').addEventListener('click', handleScanManual);
  document.getElementById('btnSyncNow').addEventListener('click', handleManualSync);

  document.getElementById('openDashboard').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: DEFAULT_DASHBOARD_URL });
  });

  document.getElementById('openSettings').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });
});

async function checkBackendStatus() {
  const statusPill = document.getElementById('statusPill');
  const statusText = document.getElementById('statusText');

  try {
    const res = await fetch(`${apiBaseUrl}/api/health`, { method: 'GET' });
    if (res.ok) {
      statusPill.className = 'status-pill';
      statusText.innerText = 'ONLINE';
    } else {
      statusPill.className = 'status-pill offline';
      statusText.innerText = 'DEGRADED';
    }
  } catch (err) {
    statusPill.className = 'status-pill offline';
    statusText.innerText = 'OFFLINE';
  }
}

async function loadProtectionTelemetry() {
  const badge = document.getElementById('rulesCountBadge');
  const syncLabel = document.getElementById('syncStatusLabel');

  try {
    chrome.runtime.sendMessage({ action: 'GET_PROTECTION_STATUS' }, (res) => {
      if (chrome.runtime.lastError || !res) {
        badge.innerText = 'Shield Offline';
        syncLabel.innerText = 'DNR Inactive';
        return;
      }

      badge.innerText = `${res.activeRulesCount} Rules Active`;
      if (res.lastSyncStatus === 'SUCCESS') {
        const timeStr = res.lastSyncTime ? new Date(res.lastSyncTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recently';
        syncLabel.innerText = `Synced: ${timeStr} (${res.lastSyncCount} IOCs)`;
      } else if (res.lastSyncStatus === 'OFFLINE_FALLBACK') {
        syncLabel.innerText = 'Threat Feed: Using Cached Rules';
        syncLabel.style.color = '#fbbf24';
      } else {
        syncLabel.innerText = 'Threat Feed: Not Synced';
      }
    });
  } catch (e) {
    badge.innerText = 'Shield Standby';
  }
}

async function handleManualSync() {
  const syncBtn = document.getElementById('btnSyncNow');
  const syncLabel = document.getElementById('syncStatusLabel');
  syncBtn.disabled = true;
  syncBtn.innerText = 'Syncing...';

  chrome.runtime.sendMessage({ action: 'SYNC_THREAT_INTEL' }, (res) => {
    syncBtn.disabled = false;
    syncBtn.innerText = 'Sync Feed';
    loadProtectionTelemetry();
  });
}

async function fetchCurrentTabUrl() {
  const urlBox = document.getElementById('currentUrlBox');
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url) {
      currentActiveUrl = tab.url;
      urlBox.innerText = currentActiveUrl;
    } else {
      urlBox.innerText = 'Unable to read active tab URL';
    }
  } catch (e) {
    urlBox.innerText = 'Permission restricted on this page';
  }
}

async function handleScanCurrent() {
  if (!currentActiveUrl || !currentActiveUrl.startsWith('http')) {
    alert('Active tab does not contain a standard HTTP or HTTPS URL to scan.');
    return;
  }
  await performScan(currentActiveUrl);
}

async function handleScanManual() {
  const input = document.getElementById('manualUrlInput');
  const url = input.value.trim();
  if (!url || !url.startsWith('http')) {
    alert('Please enter a valid HTTP or HTTPS URL to analyze.');
    return;
  }
  await performScan(url);
}

async function performScan(targetUrl) {
  const btn = document.getElementById('btnScanCurrent');
  const scanBtnText = document.getElementById('scanBtnText');

  scanBtnText.innerHTML = '<span class="loading-spinner"></span> Analyzing URL...';
  btn.disabled = true;

  try {
    const res = await fetch(`${apiBaseUrl}/api/v1/detection/url`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: targetUrl }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => null);
      showResult({
        classification: 'SERVICE_ERROR',
        risk_level: 'CRITICAL',
        risk_score: 0.0,
        recommendation: err?.detail || 'Protection service unavailable — this URL has not been verified.'
      });
      return;
    }

    const data = await res.json();
    showResult(data);
  } catch (e) {
    showResult({
      classification: 'OFFLINE',
      risk_level: 'CRITICAL',
      risk_score: 0.0,
      recommendation: 'Protection service unavailable — this URL has not been verified. Check your backend status.'
    });
  } finally {
    scanBtnText.innerText = 'Scan Current Page URL';
    btn.disabled = false;
  }
}

function showResult(data) {
  const resultPanel = document.getElementById('resultPanel');
  const verdictBadge = document.getElementById('verdictBadge');
  const scoreText = document.getElementById('scoreText');
  const explanation = document.getElementById('resultExplanation');
  const recommendation = document.getElementById('resultRecommendation');

  resultPanel.className = 'result-panel visible';
  const level = (data.risk_level || 'LOW').toUpperCase();

  if (level === 'CRITICAL' || level === 'HIGH') {
    verdictBadge.className = 'verdict-badge verdict-high';
    verdictBadge.innerText = `${level} RISK — ${data.classification || 'MALICIOUS'}`;
  } else if (level === 'MEDIUM' || level === 'SUSPICIOUS') {
    verdictBadge.className = 'verdict-badge verdict-med';
    verdictBadge.innerText = `MEDIUM RISK — ${data.classification || 'SUSPICIOUS'}`;
  } else {
    verdictBadge.className = 'verdict-badge verdict-low';
    verdictBadge.innerText = 'LOW RISK — VERIFIED LEGITIMATE';
  }

  scoreText.innerText = `${data.risk_score || 0}/100`;

  explanation.innerText = `ML Classifier & lexical features evaluated: ${data.classification}. ${
    data.analysis?.risk_indicators?.length ? 'Indicators: ' + data.analysis.risk_indicators.join(', ') : 'No anomalous homoglyphs or structural threat indicators detected.'
  }`;

  recommendation.innerText = data.recommendation || 'Proceed with normal caution.';
}
