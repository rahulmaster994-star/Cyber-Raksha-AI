// warning.js — Cyber Raksha AI
// Interstitial Threat Controller: Populates block reasons and handles explicit user override.

document.addEventListener('DOMContentLoaded', async () => {
  const params = new URLSearchParams(window.location.search);
  const targetUrl = params.get('url') || 'Unknown URL';
  let level = (params.get('level') || 'CRITICAL').toUpperCase();
  let classification = params.get('class') || 'MALICIOUS_THREAT';
  const recommendation = params.get('rec');
  const reason = params.get('reason');
  const source = params.get('source');
  const ruleId = parseInt(params.get('ruleId'), 10);

  const targetUrlBox = document.getElementById('targetUrlBox');
  const riskLevelVal = document.getElementById('riskLevelVal');
  const threatClassVal = document.getElementById('threatClassVal');
  const sourceVal = document.getElementById('sourceVal');
  const modeVal = document.getElementById('modeVal');
  const scoreVal = document.getElementById('scoreVal');
  const timestampVal = document.getElementById('timestampVal');
  const reasonsBox = document.getElementById('reasonsBox');

  const rawScore = parseFloat(params.get('score') || '90.0');
  if (scoreVal) {
    scoreVal.innerText = isNaN(rawScore) ? 'N/A' : `${rawScore.toFixed(1)} / 100`;
  }
  if (timestampVal) {
    timestampVal.innerText = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  targetUrlBox.innerText = targetUrl;
  riskLevelVal.innerText = `${level} RISK`;
  threatClassVal.innerText = classification;

  if (source === 'REALTIME_DNR' || source === 'REALTIME_DETECTOR' || source === 'REALTIME') {
    modeVal.innerText = 'In-Flight ML Interception & Dynamic Quarantine';
    modeVal.style.color = '#f87171';
    reasonsBox.innerText =
      'This destination was evaluated dynamically during navigation by the Cyber Raksha AI detection engine. Severe phishing patterns were identified; the tab was quarantined immediately to this warning page, and a network-level DNR rule was dynamically compiled.';
  } else if (source === 'DNR' || source === 'THREAT_FEED') {
    modeVal.innerText = 'Pre-Load Network Shield (Guaranteed Pre-Connection Block)';
    modeVal.style.color = '#38bdf8';
    reasonsBox.innerText =
      'This destination matches a verified threat intelligence indicator. Chromium Declarative Net Request intercepted navigation at the network layer before any TCP connection or HTTP request was sent to the destination server.';
  } else {
    modeVal.innerText = 'User-Initiated Context Menu Scan';
    modeVal.style.color = '#a78bfa';
  }

  // Check local metadata store if ruleId is provided
  if (!isNaN(ruleId)) {
    try {
      const stored = await chrome.storage.local.get(['indicatorsMetadata']);
      const metadataMap = stored.indicatorsMetadata || {};
      const meta = metadataMap[ruleId];
      if (meta) {
        if (meta.threat_type) threatClassVal.innerText = meta.threat_type;
        if (meta.severity) riskLevelVal.innerText = `${meta.severity} RISK`;
        if (meta.source_name) sourceVal.innerText = meta.source_name;
        if (meta.description) {
          reasonsBox.innerText = `${meta.description}. Confirmed in verified threat intelligence feed with confidence score ${(meta.confidence_score * 100).toFixed(0)}%. Navigation was blocked before page retrieval.`;
        }
      }
    } catch (e) {
      // Fallback to query params
    }
  }

  if (reason === 'API_OFFLINE' || reason === 'API_UNAVAILABLE') {
    threatClassVal.innerText = 'PROTECTION_UNAVAILABLE';
    riskLevelVal.innerText = 'UNVERIFIED';
    riskLevelVal.style.color = '#fbbf24';
    reasonsBox.innerText =
      'Protection service unavailable — this destination cannot be verified because the Cyber Raksha backend is currently offline. Due to security policy, unverified links are not opened automatically.';
  } else if (reason === 'UNSUPPORTED_SCHEME') {
    threatClassVal.innerText = 'UNSUPPORTED_SCHEME';
    reasonsBox.innerText =
      'Unsupported URL scheme. For your safety, Cyber Raksha only permits verified HTTP and HTTPS links.';
  } else if (recommendation) {
    reasonsBox.innerText = `${recommendation} Our detection engine evaluated this destination as a confirmed security threat.`;
  }

  // Phase A3: Dispatch verified threat interception notification to background worker
  try {
    chrome.runtime.sendMessage({
      action: 'NOTIFY_THREAT_BLOCKED',
      data: {
        url: targetUrl,
        threatType: threatClassVal.innerText || 'MALICIOUS_THREAT',
        severity: level || 'CRITICAL',
        source: source || 'DNR',
        ruleId: isNaN(ruleId) ? null : ruleId,
        reason: reasonsBox.innerText || 'Identified in verified threat intelligence database.'
      }
    });
  } catch (e) {
    // Non-blocking
  }

  // Safe Return Action
  document.getElementById('btnReturnSafe').addEventListener('click', () => {
    // Try to close tab, fallback to back or blank tab
    try {
      window.close();
    } catch (e) {
      if (window.history.length > 1) {
        window.history.back();
      } else {
        window.location.href = 'chrome://newtab';
      }
    }
  });

  // Safe URL verification helper
  function isSafeHttpUrl(urlStr) {
    if (!urlStr || typeof urlStr !== 'string') return false;
    try {
      const parsed = new URL(urlStr);
      return parsed.protocol === 'http:' || parsed.protocol === 'https:';
    } catch (e) {
      return false;
    }
  }

  // Explicit User Override Action
  const overrideBtn = document.getElementById('btnOverride');
  if (!isSafeHttpUrl(targetUrl)) {
    overrideBtn.disabled = true;
    overrideBtn.innerText = 'Bypass Disabled (Non-HTTP Scheme)';
    overrideBtn.title = 'Security policy restricts session overrides to HTTP and HTTPS web destinations.';
  }

  overrideBtn.addEventListener('click', async () => {
    if (!isSafeHttpUrl(targetUrl)) {
      alert('Security policy violation: Only verified HTTP and HTTPS web destinations can be navigated to.');
      return;
    }

    const confirmed = confirm(
      'WARNING: This destination is confirmed as malicious in threat intelligence feeds. Proceeding may compromise your accounts, personal credentials, or system security.\n\nAre you absolutely certain you want to bypass this protection and proceed at your own risk?'
    );

    if (confirmed) {
      overrideBtn.disabled = true;
      overrideBtn.innerText = 'Applying Session Bypass...';

      try {
        // Send override message to background service worker to install session allow rule
        const response = await chrome.runtime.sendMessage({
          action: 'ALLOW_OVERRIDE',
          url: targetUrl
        });

        if (response && response.success) {
          // Rule applied — navigate to target URL without getting blocked
          window.location.href = targetUrl;
        } else {
          // If background communication failed, navigate directly
          window.location.href = targetUrl;
        }
      } catch (e) {
        window.location.href = targetUrl;
      }
    }
  });
});
