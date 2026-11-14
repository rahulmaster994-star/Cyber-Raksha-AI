// background.js — Manifest V3 Service Worker for Cyber Raksha AI
// Stage C3.1: Real-Time Chrome Extension Protection
// Integrates:
// - Real-time declarative network request (DNR) threat blocking
// - Live navigation interception (chrome.webNavigation)
// - Dynamic rule generation for confirmed threats
// - Local heuristic pre-filtering and safe-domain whitelisting
// - Background threat intelligence feed synchronization
// - Device identity registration, authentication & device-scoped event telemetry
// - Fail-open resiliency (never freezes browsing on backend offline/timeout)
// - Native security notifications & centralized incident dispatch

importScripts('rules_manager.js');

const DEFAULT_API_BASE = 'https://cyberraksha-backend.onrender.com';
const DEFAULT_DASHBOARD_URL = 'https://frontend-lilac-nu-50.vercel.app';
const SYNC_ALARM_NAME = 'cyber_raksha_threat_intel_sync';
const SYNC_INTERVAL_MINUTES = 60;
const OVERRIDE_SESSION_RULE_ID = 999001;
const REALTIME_EVAL_TIMEOUT_MS = 1800; // Fast fail-open timeout

// In-memory evaluation caches (survive within service worker life)
const safeUrlCache = new Map();     // urlOrDomain -> timestamp
const blockedUrlCache = new Map();  // urlOrDomain -> { verdict, ruleId, threatType, severity, score }
const pendingVerifications = new Map(); // url -> Promise<verdict>

// ---------------------------------------------------------------------------
// 1. Extension Lifecycle Listeners
// ---------------------------------------------------------------------------

chrome.runtime.onInstalled.addListener(async () => {
  // Context menu for manual inspection
  try {
    chrome.contextMenus.create({
      id: 'cyber_raksha_check_link',
      title: 'Check with Cyber Raksha AI',
      contexts: ['link']
    });
  } catch (e) {}

  // Periodic threat intelligence sync alarm
  chrome.alarms.create(SYNC_ALARM_NAME, {
    periodInMinutes: SYNC_INTERVAL_MINUTES
  });

  // Initialize or synchronize device registration
  await initDeviceRegistration();

  // Initial threat intelligence rule compilation
  await syncThreatIntelligenceRules();
});

chrome.runtime.onStartup.addListener(async () => {
  await initDeviceRegistration();
  await syncThreatIntelligenceRules();
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === SYNC_ALARM_NAME) {
    await syncThreatIntelligenceRules();
  }
});

// ---------------------------------------------------------------------------
// 2. Configuration & Device Registration (Phase F)
// ---------------------------------------------------------------------------

async function getApiBase() {
  try {
    const stored = await chrome.storage.sync.get(['apiUrl']);
    return (stored.apiUrl || DEFAULT_API_BASE).replace(/\/+$/, '');
  } catch (e) {
    return DEFAULT_API_BASE;
  }
}

async function getDashboardUrl() {
  try {
    const stored = await chrome.storage.sync.get(['dashboardUrl']);
    return (stored.dashboardUrl || DEFAULT_DASHBOARD_URL).replace(/\/+$/, '');
  } catch (e) {
    return DEFAULT_DASHBOARD_URL;
  }
}

/**
 * Ensures this browser instance has a registered device identity on the backend.
 * Generates and stores a unique UUIDv4 device identifier and secure device token.
 */
async function initDeviceRegistration() {
  const local = await chrome.storage.local.get(['device_id', 'device_token', 'device_registered_at']);
  let deviceId = local.device_id;
  let deviceToken = local.device_token;

  if (!deviceId) {
    // Generate UUIDv4 compliant with backend hex regex
    deviceId = typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : generateFallbackUuid();
    await chrome.storage.local.set({ device_id: deviceId });
  }

  // Attempt registration with backend if token missing
  if (!deviceToken) {
    const apiBase = await getApiBase();
    try {
      const response = await fetch(`${apiBase}/api/v1/devices/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_id: deviceId,
          device_name: 'Chrome Browser Shield (Chromium Extension)',
          app_version: '1.3.0'
        })
      });

      if (response.ok) {
        const data = await response.json();
        deviceToken = data.device_token;
        await chrome.storage.local.set({
          device_token: deviceToken,
          device_registered_at: new Date().toISOString(),
          device_status: 'REGISTERED'
        });
      } else {
        await chrome.storage.local.set({ device_status: 'REGISTRATION_PENDING' });
      }
    } catch (err) {
      await chrome.storage.local.set({ device_status: 'OFFLINE_PENDING' });
    }
  }

  return { deviceId, deviceToken };
}

function generateFallbackUuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// ---------------------------------------------------------------------------
// 3. Real-Time Navigation Protection (Phase B & C)
// ---------------------------------------------------------------------------

if (chrome.webNavigation && chrome.webNavigation.onBeforeNavigate) {
  chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
    // Only inspect top-level main frame navigations
    if (details.frameId !== 0) return;

    const rawUrl = details.url;
    if (!rawUrl) return;

    // Filter out internal and non-HTTP schemes
    if (rawUrl.startsWith('chrome://') ||
        rawUrl.startsWith('chrome-extension://') ||
        rawUrl.startsWith('about:') ||
        rawUrl.startsWith('file://') ||
        rawUrl.startsWith('devtools://') ||
        rawUrl.startsWith('edge://') ||
        rawUrl.startsWith('data:') ||
        rawUrl.startsWith('blob:')) {
      return;
    }

    let parsed;
    try {
      parsed = new URL(rawUrl);
    } catch (e) {
      return;
    }

    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return;
    }

    const hostname = parsed.hostname.toLowerCase();

    // Whitelist check: instant allowance for verified infrastructure (0ms latency impact)
    if (typeof isWhitelistedSafeDomain === 'function' && isWhitelistedSafeDomain(hostname)) {
      return;
    }

    // Session override check: if user chose to proceed in this session, do not block
    const isOverridden = await isSessionOverridden(hostname);
    if (isOverridden) {
      return;
    }

    // Check fast in-memory safe cache (< 30 minutes)
    const now = Date.now();
    const cachedSafe = safeUrlCache.get(hostname) || safeUrlCache.get(rawUrl);
    if (cachedSafe && (now - cachedSafe) < 1800000) {
      return;
    }

    // Check fast in-memory blocked cache
    const cachedBlocked = blockedUrlCache.get(hostname) || blockedUrlCache.get(rawUrl);
    if (cachedBlocked) {
      await interceptNavigation(details.tabId, rawUrl, cachedBlocked);
      return;
    }

    // Check persistent threat intelligence indicators metadata (synced feed)
    const matchInFeed = await checkThreatIntelligenceFeed(rawUrl, hostname);
    if (matchInFeed) {
      blockedUrlCache.set(hostname, matchInFeed);
      await interceptNavigation(details.tabId, rawUrl, matchInFeed);
      return;
    }

    // Fast heuristic pre-check before hitting backend
    const isSuspicious = evaluateHeuristics(rawUrl, hostname);

    // If suspicious or unknown origin, perform live backend evaluation
    if (isSuspicious) {
      evaluateAndProtectUrl(details.tabId, rawUrl, hostname);
    }
  });
}

/**
 * Checks local threat intelligence metadata store for domain or URL match
 */
async function checkThreatIntelligenceFeed(rawUrl, hostname) {
  try {
    const stored = await chrome.storage.local.get(['indicatorsMetadata']);
    const metadataMap = stored.indicatorsMetadata || {};

    for (const ruleId in metadataMap) {
      const meta = metadataMap[ruleId];
      if (!meta) continue;

      if (meta.indicator_type === 'DOMAIN' && meta.indicator_value === hostname) {
        return {
          threatType: meta.threat_type || 'PHISHING',
          severity: meta.severity || 'CRITICAL',
          riskScore: meta.confidence_score ? meta.confidence_score * 100 : 95.0,
          description: meta.description || 'Threat feed confirmed malicious domain',
          source: 'THREAT_FEED',
          ruleId: parseInt(ruleId, 10)
        };
      }

      if (meta.indicator_type === 'URL' && rawUrl.startsWith(meta.indicator_value)) {
        return {
          threatType: meta.threat_type || 'PHISHING',
          severity: meta.severity || 'CRITICAL',
          riskScore: meta.confidence_score ? meta.confidence_score * 100 : 95.0,
          description: meta.description || 'Threat feed confirmed malicious URL',
          source: 'THREAT_FEED',
          ruleId: parseInt(ruleId, 10)
        };
      }
    }
  } catch (e) {}
  return null;
}

/**
 * Heuristic pre-screener for lexical phishing signals
 */
function evaluateHeuristics(rawUrl, hostname) {
  const lower = rawUrl.toLowerCase();
  const SUSPICIOUS_KEYWORDS = [
    'sbi', 'hdfc', 'icici', 'axis', 'pnb', 'bank',
    'cbi', 'police', 'arrest', 'cybercrime', 'enforcement',
    'kyc', 'pan-card', 'aadhaar', 'income-tax', 'incometax',
    'verify-account', 'secure-login', 'netbanking-update', 'urgent-action',
    'otp-verify', 'claim-reward', 'lottery'
  ];

  const SUSPICIOUS_TLDS = ['.xyz', '.top', '.tk', '.ml', '.ga', '.cf', '.gq', '.buzz', '.club', '.work', '.cam', '.rest'];

  // Check IP address hostname
  if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(hostname)) {
    return true;
  }

  // Check suspicious TLDs
  for (const tld of SUSPICIOUS_TLDS) {
    if (hostname.endsWith(tld)) return true;
  }

  // Check brand impersonation / scam keywords
  for (const kw of SUSPICIOUS_KEYWORDS) {
    if (hostname.includes(kw) || lower.includes(`/${kw}`) || lower.includes(`-${kw}`)) {
      return true;
    }
  }

  // Check excessive hyphens or subdomains (phishing obfuscation)
  if ((hostname.match(/-/g) || []).length >= 2 || (hostname.match(/\./g) || []).length >= 3) {
    return true;
  }

  return false;
}

/**
 * Live URL evaluation against Cyber Raksha AI backend with fail-open timeout
 */
async function evaluateAndProtectUrl(tabId, rawUrl, hostname) {
  // Deduplicate inflight checks for identical URL
  if (pendingVerifications.has(rawUrl)) {
    return pendingVerifications.get(rawUrl);
  }

  const sanitized = typeof sanitizeUrl === 'function' ? sanitizeUrl(rawUrl) : rawUrl;
  const promise = (async () => {
    const apiBase = await getApiBase();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REALTIME_EVAL_TIMEOUT_MS);

    try {
      const response = await fetch(`${apiBase}/api/v1/detection/url`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: sanitized }),
        signal: controller.signal
      });
      clearTimeout(timeout);

      if (!response.ok) {
        // Backend returned non-200: fail open to avoid disrupting user
        safeUrlCache.set(hostname, Date.now());
        return;
      }

      const result = await response.json();
      const level = (result.risk_level || 'LOW').toUpperCase();
      const confidence = typeof result.confidence === 'number' ? result.confidence : 0.5;

      // Policy: Block confirmed CRITICAL or high-confidence HIGH
      if (level === 'CRITICAL' || (level === 'HIGH' && confidence >= 0.70)) {
        const threatData = {
          threatType: result.classification || 'PHISHING',
          severity: level,
          riskScore: result.risk_score || 90.0,
          description: result.recommendation || `Automated ML phishing classifier identified critical risk (${result.classification})`,
          source: 'REALTIME_DETECTOR',
          ruleId: hashIndicatorToId ? hashIndicatorToId('URL', rawUrl) : 950001
        };

        // Cache as blocked
        blockedUrlCache.set(hostname, threatData);
        blockedUrlCache.set(rawUrl, threatData);

        // Dynamically install DNR blocking rule for network-level protection
        if (typeof createDynamicBlockRule === 'function') {
          const extensionBase = chrome.runtime.getURL('/');
          const dnrRule = createDynamicBlockRule(
            rawUrl,
            threatData.threatType,
            threatData.severity,
            threatData.ruleId,
            extensionBase
          );

          try {
            await chrome.declarativeNetRequest.updateDynamicRules({
              removeRuleIds: [threatData.ruleId],
              addRules: [dnrRule]
            });
          } catch (ruleErr) {}
        }

        // Intercept navigation
        await interceptNavigation(tabId, rawUrl, threatData);
      } else {
        // Safe or low risk: cache to speed up subsequent requests
        safeUrlCache.set(hostname, Date.now());
      }
    } catch (err) {
      // Backend unavailable or timeout: FAIL OPEN (never freeze browsing)
      safeUrlCache.set(hostname, Date.now());
    } finally {
      pendingVerifications.delete(rawUrl);
    }
  })();

  pendingVerifications.set(rawUrl, promise);
  return promise;
}

/**
 * Redirects tab to extension-owned interstitial warning page and dispatches security event
 */
async function interceptNavigation(tabId, targetUrl, threatData) {
  const warningUrl = chrome.runtime.getURL(
    `warning.html?url=${encodeURIComponent(targetUrl)}&level=${encodeURIComponent(threatData.severity)}&score=${encodeURIComponent(threatData.riskScore || 90)}&class=${encodeURIComponent(threatData.threatType)}&source=${encodeURIComponent(threatData.source || 'REALTIME')}&ruleId=${encodeURIComponent(threatData.ruleId || '')}`
  );

  try {
    if (tabId && chrome.tabs && chrome.tabs.update) {
      await chrome.tabs.update(tabId, { url: warningUrl });
    }
  } catch (e) {}

  // Trigger alert and backend event ingestion
  await showSecurityNotification({
    url: targetUrl,
    threatType: threatData.threatType,
    severity: threatData.severity,
    riskScore: threatData.riskScore,
    source: threatData.source || 'REALTIME_SHIELD',
    ruleId: threatData.ruleId,
    reason: threatData.description
  });
}

async function isSessionOverridden(hostname) {
  try {
    const rules = await chrome.declarativeNetRequest.getSessionRules();
    for (const r of rules) {
      if (r.action && r.action.type === 'allow' && r.condition && r.condition.urlFilter) {
        if (r.condition.urlFilter.includes(hostname)) return true;
      }
    }
  } catch (e) {}
  return false;
}

// ---------------------------------------------------------------------------
// 4. Threat Intelligence Feed Synchronization (Phase E)
// ---------------------------------------------------------------------------

async function syncThreatIntelligenceRules() {
  const apiBase = await getApiBase();
  const timestamp = new Date().toISOString();

  try {
    const response = await fetch(`${apiBase}/api/v1/intel/indicators?limit=500`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) {
      await chrome.storage.local.set({
        last_sync_status: 'OFFLINE_FALLBACK',
        last_sync_attempt: timestamp,
        last_sync_error: `HTTP ${response.status}: Failed to retrieve threat feed.`
      });
      return { success: false, reason: `HTTP_${response.status}` };
    }

    const indicators = await response.json();
    if (!Array.isArray(indicators)) {
      throw new Error('Invalid indicators payload format; expected array.');
    }

    const currentRules = await chrome.declarativeNetRequest.getDynamicRules();
    const extensionBase = chrome.runtime.getURL('/');

    const delta = syncRulesDelta(currentRules, indicators, extensionBase);

    await chrome.declarativeNetRequest.updateDynamicRules({
      removeRuleIds: delta.removeRuleIds,
      addRules: delta.addRules
    });

    await chrome.storage.local.set({
      indicatorsMetadata: delta.metadataMap,
      last_sync_status: 'SUCCESS',
      last_sync_time: timestamp,
      last_sync_count: delta.addRules.length,
      last_sync_stats: delta.stats
    });

    return { success: true, count: delta.addRules.length, stats: delta.stats };
  } catch (err) {
    // Preserve previously cached rules on network failure
    await chrome.storage.local.set({
      last_sync_status: 'OFFLINE_FALLBACK',
      last_sync_attempt: timestamp,
      last_sync_error: err.message || 'Network disconnected or backend offline.'
    });
    return { success: false, reason: 'OFFLINE_FALLBACK', error: err.message };
  }
}

// ---------------------------------------------------------------------------
// 5. User Override Management (Phase D)
// ---------------------------------------------------------------------------

async function handleUserOverride(targetUrl) {
  try {
    const allowRule = createOverrideAllowRule(targetUrl, OVERRIDE_SESSION_RULE_ID);

    await chrome.declarativeNetRequest.updateSessionRules({
      removeRuleIds: [OVERRIDE_SESSION_RULE_ID],
      addRules: [allowRule]
    });

    // Clear from blocked cache for this session
    try {
      const parsed = new URL(targetUrl);
      blockedUrlCache.delete(parsed.hostname.toLowerCase());
      blockedUrlCache.delete(targetUrl);
    } catch (e) {}

    const stored = await chrome.storage.local.get(['overrideEvents']);
    const events = stored.overrideEvents || [];
    events.push({
      url: typeof sanitizeUrl === 'function' ? sanitizeUrl(targetUrl) : targetUrl,
      timestamp: new Date().toISOString(),
      override_type: 'USER_CONFIRMED_SESSION_BYPASS'
    });
    if (events.length > 50) events.shift();
    await chrome.storage.local.set({ overrideEvents: events });

    return { success: true, ruleId: OVERRIDE_SESSION_RULE_ID };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// ---------------------------------------------------------------------------
// 6. Security Event & Notification Engine (Phase F & J)
// ---------------------------------------------------------------------------

const NOTIFICATION_SEVERITY_RANKS = { 'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4 };
const recentNotificationDomains = new Map();

async function showSecurityNotification(threatData) {
  if (!threatData || !threatData.url) return;

  let domain = 'unknown-destination';
  try {
    domain = new URL(threatData.url).hostname;
  } catch (e) {
    domain = threatData.url.replace(/^https?:\/\//i, '').split('/')[0];
  }

  // Rate limiting per domain (30 seconds)
  const now = Date.now();
  const lastNotified = recentNotificationDomains.get(domain);
  if (lastNotified && now - lastNotified < 30000) {
    return;
  }
  recentNotificationDomains.set(domain, now);

  const stored = await chrome.storage.local.get(['notificationPreferences', 'device_id', 'device_token']);
  const prefs = stored.notificationPreferences || { enabled: true, min_severity: 'LOW' };
  const deviceId = stored.device_id || null;
  const deviceToken = stored.device_token || null;

  if (prefs.enabled) {
    const threatSeverity = (threatData.severity || 'CRITICAL').toUpperCase();
    const incomingRank = NOTIFICATION_SEVERITY_RANKS[threatSeverity] || 1;
    const minRank = NOTIFICATION_SEVERITY_RANKS[(prefs.min_severity || 'LOW').toUpperCase()] || 1;

    if (incomingRank >= minRank && chrome.notifications && chrome.notifications.create) {
      chrome.notifications.create(`cyber_raksha_${Date.now()}`, {
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/icon128.png'),
        title: 'CYBER RAKSHA AI — THREAT INTERCEPTED',
        message: `Destination: ${domain}\nSeverity: ${threatSeverity}\nThreat: ${threatData.threatType || 'MALICIOUS_URL'}\nStatus: Navigation blocked successfully.`,
        priority: threatSeverity === 'CRITICAL' ? 2 : 1,
        requireInteraction: threatSeverity === 'CRITICAL'
      });
    }
  }

  // Forward SecurityEvent to backend central risk engine
  const sanitizedUrl = typeof sanitizeUrl === 'function' ? sanitizeUrl(threatData.url) : threatData.url;
  const apiBase = await getApiBase();
  const headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  };
  if (deviceToken) {
    headers['Authorization'] = `Bearer ${deviceToken}`;
  }

  try {
    await fetch(`${apiBase}/api/v1/security/events`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        event_type: 'BROWSER_BLOCKED_URL',
        severity: (threatData.severity || 'HIGH').toUpperCase(),
        source_component: 'BROWSER_EXTENSION',
        device_id: deviceId,
        threat_indicator: sanitizedUrl,
        risk_score: threatData.riskScore || 90.0,
        detection_reason: threatData.reason || `Browser Shield intercepted confirmed threat (${threatData.threatType})`,
        description: `Blocked navigation to ${sanitizedUrl} (${threatData.threatType || 'PHISHING'})`
      })
    });
  } catch (err) {}

  // Forward to backend notifications API
  try {
    await fetch(`${apiBase}/api/v1/notifications`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        title: `Malicious Website Intercepted: ${domain}`,
        message: `Navigation to ${sanitizedUrl} was blocked. Threat: ${threatData.threatType || 'PHISHING'}`,
        severity: (threatData.severity || 'HIGH').toUpperCase(),
        category: 'MALICIOUS_WEBSITE',
        target_domain: domain,
        recommended_action: 'Navigation was blocked. Avoid sharing credentials on this domain.',
        source_component: 'BROWSER_EXTENSION',
        metadata_json: {
          url: sanitizedUrl,
          rule_id: threatData.ruleId,
          device_id: deviceId,
          source: threatData.source || 'BROWSER_SHIELD'
        }
      })
    });
  } catch (err) {}
}

// Notification Click Handler: Opens Dashboard
if (chrome.notifications && chrome.notifications.onClicked) {
  chrome.notifications.onClicked.addListener(async () => {
    const dashUrl = await getDashboardUrl();
    chrome.tabs.create({ url: dashUrl });
  });
}

// ---------------------------------------------------------------------------
// 7. Message Communication Handler
// ---------------------------------------------------------------------------

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'SYNC_THREAT_INTEL') {
    syncThreatIntelligenceRules().then(sendResponse);
    return true;
  }

  if (message.action === 'GET_PROTECTION_STATUS') {
    (async () => {
      const dynamicRules = await chrome.declarativeNetRequest.getDynamicRules();
      const sessionRules = await chrome.declarativeNetRequest.getSessionRules();
      const local = await chrome.storage.local.get([
        'indicatorsMetadata',
        'last_sync_status',
        'last_sync_time',
        'last_sync_count',
        'last_sync_error',
        'device_id',
        'device_status'
      ]);
      sendResponse({
        activeRulesCount: dynamicRules.length,
        sessionOverridesCount: sessionRules.length,
        lastSyncStatus: local.last_sync_status || 'NOT_SYNCED',
        lastSyncTime: local.last_sync_time || null,
        lastSyncCount: local.last_sync_count || 0,
        lastSyncError: local.last_sync_error || null,
        deviceId: local.device_id || null,
        deviceStatus: local.device_status || 'STANDBY'
      });
    })();
    return true;
  }

  if (message.action === 'ALLOW_OVERRIDE') {
    handleUserOverride(message.url).then(sendResponse);
    return true;
  }

  if (message.action === 'NOTIFY_THREAT_BLOCKED') {
    showSecurityNotification(message.data);
    sendResponse({ success: true });
    return true;
  }

  if (message.action === 'GET_DEVICE_INFO') {
    chrome.storage.local.get(['device_id', 'device_status', 'device_registered_at']).then(sendResponse);
    return true;
  }

  if (message.action === 'CHECK_URL_REALTIME') {
    (async () => {
      const targetUrl = message.url;
      const parsed = new URL(targetUrl);
      const isSuspicious = evaluateHeuristics(targetUrl, parsed.hostname.toLowerCase());
      const apiBase = await getApiBase();
      try {
        const response = await fetch(`${apiBase}/api/v1/detection/url`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: typeof sanitizeUrl === 'function' ? sanitizeUrl(targetUrl) : targetUrl })
        });
        if (response.ok) {
          const data = await response.json();
          sendResponse({ success: true, result: data });
        } else {
          sendResponse({ success: false, heuristicOnly: isSuspicious });
        }
      } catch (e) {
        sendResponse({ success: false, error: e.message, heuristicOnly: isSuspicious });
      }
    })();
    return true;
  }
});

// ---------------------------------------------------------------------------
// 8. User-Assisted Context-Menu Inspection (Preserved & Enhanced)
// ---------------------------------------------------------------------------

chrome.contextMenus.onClicked.addListener(async (info) => {
  if (info.menuItemId === 'cyber_raksha_check_link' && info.linkUrl) {
    const targetUrl = info.linkUrl.trim();

    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      chrome.tabs.create({
        url: chrome.runtime.getURL(`warning.html?url=${encodeURIComponent(targetUrl)}&reason=UNSUPPORTED_SCHEME`)
      });
      return;
    }

    const apiBase = await getApiBase();
    const sanitized = typeof sanitizeUrl === 'function' ? sanitizeUrl(targetUrl) : targetUrl;

    try {
      const response = await fetch(`${apiBase}/api/v1/detection/url`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: sanitized })
      });

      if (!response.ok) {
        chrome.tabs.create({
          url: chrome.runtime.getURL(`warning.html?url=${encodeURIComponent(targetUrl)}&level=CRITICAL&score=0&reason=API_UNAVAILABLE`)
        });
        return;
      }

      const result = await response.json();
      const level = (result.risk_level || 'LOW').toUpperCase();

      if (level === 'CRITICAL' || level === 'HIGH') {
        chrome.tabs.create({
          url: chrome.runtime.getURL(
            `warning.html?url=${encodeURIComponent(targetUrl)}&level=${level}&score=${result.risk_score}&class=${encodeURIComponent(result.classification)}&rec=${encodeURIComponent(result.recommendation)}`
          )
        });
      } else if (level === 'MEDIUM' || level === 'SUSPICIOUS') {
        chrome.tabs.create({
          url: chrome.runtime.getURL(
            `warning.html?url=${encodeURIComponent(targetUrl)}&level=${level}&score=${result.risk_score}&class=${encodeURIComponent(result.classification)}&rec=${encodeURIComponent(result.recommendation)}&allow_override=true`
          )
        });
      } else {
        chrome.tabs.create({ url: targetUrl });
      }
    } catch (err) {
      chrome.tabs.create({
        url: chrome.runtime.getURL(`warning.html?url=${encodeURIComponent(targetUrl)}&level=CRITICAL&score=0&reason=API_OFFLINE`)
      });
    }
  }
});
