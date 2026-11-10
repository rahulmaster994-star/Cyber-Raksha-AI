// background.js — Manifest V3 Service Worker for Cyber Raksha AI
// Integrates Declarative Net Request (DNR) automated threat blocking,
// hourly threat intelligence synchronization, and user-assisted context-menu scanning.

importScripts('rules_manager.js');

const DEFAULT_API_BASE = 'http://127.0.0.1:8000';
const SYNC_ALARM_NAME = 'cyber_raksha_threat_intel_sync';
const SYNC_INTERVAL_MINUTES = 60;
const OVERRIDE_SESSION_RULE_ID = 999001;

// ---------------------------------------------------------------------------
// 1. Extension Lifecycle Listeners
// ---------------------------------------------------------------------------

chrome.runtime.onInstalled.addListener(async () => {
  // Setup manual link inspection context menu
  chrome.contextMenus.create({
    id: 'cyber_raksha_check_link',
    title: 'Check with Cyber Raksha AI',
    contexts: ['link']
  });

  // Setup periodic threat intelligence sync alarm
  chrome.alarms.create(SYNC_ALARM_NAME, {
    periodInMinutes: SYNC_INTERVAL_MINUTES
  });

  // Initial threat intelligence rule compilation
  await syncThreatIntelligenceRules();
});

chrome.runtime.onStartup.addListener(async () => {
  // Sync on browser start to refresh active rules
  await syncThreatIntelligenceRules();
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === SYNC_ALARM_NAME) {
    await syncThreatIntelligenceRules();
  }
});

// ---------------------------------------------------------------------------
// 2. Threat Intelligence DNR Dynamic Rules Synchronization
// ---------------------------------------------------------------------------

async function getApiBase() {
  try {
    const stored = await chrome.storage.sync.get(['apiUrl']);
    return (stored.apiUrl || DEFAULT_API_BASE).replace(/\/+$/, '');
  } catch (e) {
    return DEFAULT_API_BASE;
  }
}

async function syncThreatIntelligenceRules() {
  const apiBase = await getApiBase();
  const timestamp = new Date().toISOString();

  try {
    const response = await fetch(`${apiBase}/api/v1/intel/indicators?limit=500`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      // Backend returned error (e.g. 500, 404)
      await chrome.storage.local.set({
        last_sync_status: 'OFFLINE_FALLBACK',
        last_sync_attempt: timestamp,
        last_sync_error: `HTTP ${response.status}: Failed to retrieve threat feed.`
      });
      // CRITICAL: Previously installed dynamic rules remain active!
      return { success: false, reason: `HTTP_${response.status}` };
    }

    const indicators = await response.json();
    if (!Array.isArray(indicators)) {
      throw new Error('Invalid indicators payload format; expected array.');
    }

    // Get currently installed dynamic rules in Chrome
    const currentRules = await chrome.declarativeNetRequest.getDynamicRules();
    const extensionBase = chrome.runtime.getURL('/');

    // Compute delta diff using rules_manager
    const delta = syncRulesDelta(currentRules, indicators, extensionBase);

    // Apply rule changes atomically in Chrome
    await chrome.declarativeNetRequest.updateDynamicRules({
      removeRuleIds: delta.removeRuleIds,
      addRules: delta.addRules
    });

    // Persist indicator metadata and sync status
    await chrome.storage.local.set({
      indicatorsMetadata: delta.metadataMap,
      last_sync_status: 'SUCCESS',
      last_sync_time: timestamp,
      last_sync_count: delta.addRules.length,
      last_sync_stats: delta.stats
    });

    return { success: true, count: delta.addRules.length, stats: delta.stats };
  } catch (err) {
    // Backend unreachable / network offline: fail safely without removing cached rules
    await chrome.storage.local.set({
      last_sync_status: 'OFFLINE_FALLBACK',
      last_sync_attempt: timestamp,
      last_sync_error: err.message || 'Network disconnected or backend offline.'
    });
    return { success: false, reason: 'OFFLINE_FALLBACK', error: err.message };
  }
}

// ---------------------------------------------------------------------------
// 3. User Override Management (Session Allow Rules)
// ---------------------------------------------------------------------------

async function handleUserOverride(targetUrl) {
  try {
    const allowRule = createOverrideAllowRule(targetUrl, OVERRIDE_SESSION_RULE_ID);

    // Install session allow rule (higher priority than block rules)
    await chrome.declarativeNetRequest.updateSessionRules({
      removeRuleIds: [OVERRIDE_SESSION_RULE_ID],
      addRules: [allowRule]
    });

    // Record override audit log locally
    const stored = await chrome.storage.local.get(['overrideEvents']);
    const events = stored.overrideEvents || [];
    events.push({
      url: targetUrl,
      timestamp: new Date().toISOString(),
      override_type: 'USER_CONFIRMED_SESSION_BYPASS'
    });
    // Keep last 50 events
    if (events.length > 50) events.shift();
    await chrome.storage.local.set({ overrideEvents: events });

    return { success: true, ruleId: OVERRIDE_SESSION_RULE_ID };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// ---------------------------------------------------------------------------
// 4. Message Communication Handler (Popup, Warning & Options Pages)
// ---------------------------------------------------------------------------

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'SYNC_THREAT_INTEL') {
    syncThreatIntelligenceRules().then(sendResponse);
    return true; // Keep channel open for async response
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
        'last_sync_error'
      ]);
      sendResponse({
        activeRulesCount: dynamicRules.length,
        sessionOverridesCount: sessionRules.length,
        lastSyncStatus: local.last_sync_status || 'NOT_SYNCED',
        lastSyncTime: local.last_sync_time || null,
        lastSyncCount: local.last_sync_count || 0,
        lastSyncError: local.last_sync_error || null
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
});

// ---------------------------------------------------------------------------
// 5. Existing User-Assisted Context-Menu Inspection (Preserved)
// ---------------------------------------------------------------------------

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'cyber_raksha_check_link' && info.linkUrl) {
    const targetUrl = info.linkUrl.trim();

    // Scheme validation
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      chrome.tabs.create({
        url: chrome.runtime.getURL(`warning.html?url=${encodeURIComponent(targetUrl)}&reason=UNSUPPORTED_SCHEME`)
      });
      return;
    }

    const apiBase = await getApiBase();

    try {
      const response = await fetch(`${apiBase}/api/v1/detection/url`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: targetUrl })
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
        // Safe — open link directly
        chrome.tabs.create({ url: targetUrl });
      }
    } catch (err) {
      chrome.tabs.create({
        url: chrome.runtime.getURL(`warning.html?url=${encodeURIComponent(targetUrl)}&level=CRITICAL&score=0&reason=API_OFFLINE`)
      });
    }
  }
});

// ---------------------------------------------------------------------------
// 6. Phase A3: Intelligent Security Notification & Alert Engine
// ---------------------------------------------------------------------------

const NOTIFICATION_SEVERITY_RANKS = { 'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4 };
const recentNotificationDomains = new Map(); // domain -> timestamp (for 30s rate-limiting)

async function showSecurityNotification(threatData) {
  if (!threatData || !threatData.url) return;

  let domain = 'unknown-destination';
  try {
    domain = new URL(threatData.url).hostname;
  } catch (e) {
    domain = threatData.url.replace(/^https?:\/\//i, '').split('/')[0];
  }

  // Rate-limiting check by domain (30-second cooldown)
  const now = Date.now();
  const lastNotified = recentNotificationDomains.get(domain);
  if (lastNotified && now - lastNotified < 30000) {
    return; // Rate limit duplicate notifications for the same domain
  }
  recentNotificationDomains.set(domain, now);

  // Clean old rate limit entries
  for (const [d, ts] of recentNotificationDomains.entries()) {
    if (now - ts > 60000) recentNotificationDomains.delete(d);
  }

  // Read preferences from local storage
  const stored = await chrome.storage.local.get(['notificationPreferences']);
  const prefs = stored.notificationPreferences || {
    enabled: true,
    min_severity: 'LOW',
    sound: false
  };

  if (!prefs.enabled) return;

  const threatSeverity = (threatData.severity || 'CRITICAL').toUpperCase();
  const incomingRank = NOTIFICATION_SEVERITY_RANKS[threatSeverity] || 1;
  const minRank = NOTIFICATION_SEVERITY_RANKS[(prefs.min_severity || 'LOW').toUpperCase()] || 1;

  if (incomingRank < minRank) {
    return; // Below user's configured notification threshold
  }

  const notificationId = `cyber_raksha_${Date.now()}`;
  const threatType = threatData.threatType || 'MALICIOUS_THREAT';

  if (chrome.notifications && chrome.notifications.create) {
    chrome.notifications.create(notificationId, {
      type: 'basic',
      iconUrl: chrome.runtime.getURL('icons/icon128.png'),
      title: 'CYBER RAKSHA AI — MALICIOUS WEBSITE BLOCKED',
      message: `Website: ${domain}\nRisk Level: ${threatSeverity}\nReason: ${threatType}\nAction: Navigation blocked successfully.`,
      priority: threatSeverity === 'CRITICAL' ? 2 : (threatSeverity === 'HIGH' ? 1 : 0),
      requireInteraction: threatSeverity === 'CRITICAL'
    });
  }

  // Forward event to Cyber Raksha AI unified security event pipeline
  try {
    const apiBase = await getApiBase();
    await fetch(`${apiBase}/api/v1/security/events`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        event_type: 'BROWSER_BLOCKED_URL',
        severity: threatSeverity,
        source_component: 'BROWSER_EXTENSION',
        threat_indicator: threatData.url,
        risk_score: threatSeverity === 'CRITICAL' ? 95.0 : (threatSeverity === 'HIGH' ? 80.0 : 50.0),
        detection_reason: `Pre-load Declarative Net Request blocked navigation to ${domain}. Reason: ${threatType}`,
        description: `Blocked navigation to ${threatData.url} (${threatType})`
      })
    });
  } catch (err) {
    // Non-blocking if backend is offline
  }

  // Forward event to Cyber Raksha AI backend notification API
  try {
    const apiBase = await getApiBase();
    await fetch(`${apiBase}/api/v1/notifications`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: `Malicious Website Blocked: ${domain}`,
        message: `Navigation to ${threatData.url} was blocked before page load. Reason: ${threatType}`,
        severity: threatSeverity,
        category: 'MALICIOUS_WEBSITE',
        target_domain: domain,
        recommended_action: 'Navigation was blocked successfully. Avoid sharing credentials on this origin.',
        source_component: 'BROWSER_EXTENSION',
        metadata_json: {
          url: threatData.url,
          rule_id: threatData.ruleId,
          source: threatData.source || 'DNR'
        }
      })
    });
  } catch (err) {
    // Non-blocking if backend is offline
  }
}

// Notification Click Handler: Opens Dashboard Control Center
if (chrome.notifications && chrome.notifications.onClicked) {
  chrome.notifications.onClicked.addListener(async (notificationId) => {
    chrome.tabs.create({ url: 'http://localhost:5173/?tab=dashboard' });
  });
}
