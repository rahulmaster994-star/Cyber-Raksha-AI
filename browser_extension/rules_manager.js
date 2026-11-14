/**
 * rules_manager.js — Cyber Raksha AI
 * Manifest V3 Declarative Net Request (DNR) Dynamic Rules Manager.
 * 
 * Converts verified threat intelligence indicators (domains, URLs, IPs)
 * into high-performance Chromium declarativeNetRequest blocking rules.
 * 
 * Works in both Chrome Extension Service Workers (via importScripts)
 * and Node.js testing environments.
 */

// Multi-tenant and shared hosting domains that must NEVER be blocked as an entire domain
const SHARED_DOMAINS = new Set([
  'github.com',
  'raw.githubusercontent.com',
  'github.io',
  'gitlab.com',
  'drive.google.com',
  'docs.google.com',
  'sites.google.com',
  'dropbox.com',
  'onedrive.live.com',
  's3.amazonaws.com',
  'storage.googleapis.com',
  'firebaseapp.com',
  'web.app',
  'vercel.app',
  'netlify.app',
  'pages.dev',
  'workers.dev',
  'glitch.me',
  'cloudflare.com',
  'azurewebsites.net',
  'blogspot.com',
  'wordpress.com',
  'wixsite.com',
  'medium.com'
]);

// Maximum dynamic rules to maintain (Chrome limit is 5000; regex rules cap is 1000)
const MAX_DYNAMIC_RULES = 900;
const MIN_CONFIDENCE_THRESHOLD = 0.80;
const VALID_SEVERITIES = new Set(['CRITICAL', 'HIGH', 'MEDIUM']);
const VALID_INDICATOR_TYPES = new Set(['URL', 'DOMAIN', 'IP']);

/**
 * Deterministic hash converting indicator type + value to a positive integer ID (range 1000 to 899999)
 */
function hashIndicatorToId(type, value) {
  const str = `${type.toUpperCase()}:${value.toLowerCase().trim()}`;
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash = hash & 0x7FFFFFFF;
  }
  return 1000 + (hash % 899000);
}

/**
 * Escapes special characters for RE2 regular expressions
 */
function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Validates a threat intelligence indicator against strict criteria:
 * - Active flag
 * - Confidence threshold >= 0.80
 * - Shared hosting domain protection
 * - Scheme and format validation
 */
function validateIndicator(indicator) {
  if (!indicator || typeof indicator !== 'object') {
    return { valid: false, reason: 'INVALID_OBJECT' };
  }

  const rawType = (indicator.indicator_type || '').toUpperCase().trim();
  const rawValue = (indicator.indicator_value || '').trim();

  if (!VALID_INDICATOR_TYPES.has(rawType)) {
    return { valid: false, reason: `UNSUPPORTED_TYPE_${rawType}` };
  }

  if (!rawValue || rawValue.length < 3) {
    return { valid: false, reason: 'EMPTY_OR_SHORT_VALUE' };
  }

  // Check active flag
  if (indicator.is_active === false) {
    return { valid: false, reason: 'INDICATOR_INACTIVE' };
  }

  // Check confidence threshold
  const confidence = typeof indicator.confidence_score === 'number'
    ? indicator.confidence_score
    : parseFloat(indicator.confidence_score || '0.9');

  if (isNaN(confidence) || confidence < MIN_CONFIDENCE_THRESHOLD) {
    return { valid: false, reason: 'LOW_CONFIDENCE' };
  }

  const severity = (indicator.severity || 'HIGH').toUpperCase().trim();
  if (!VALID_SEVERITIES.has(severity)) {
    return { valid: false, reason: `UNSUPPORTED_SEVERITY_${severity}` };
  }

  const threatType = (indicator.threat_type || 'MALICIOUS_THREAT').toUpperCase().trim();
  const sourceName = indicator.source_name || 'THREAT_FEED';

  // Specific type validations
  if (rawType === 'DOMAIN') {
    let cleanDomain = rawValue.toLowerCase();
    // Strip scheme if present
    cleanDomain = cleanDomain.replace(/^https?:\/\//i, '').split('/')[0].split(':')[0].trim();

    if (!cleanDomain || !cleanDomain.includes('.') || cleanDomain.includes(' ') || cleanDomain.startsWith('.') || cleanDomain.endsWith('.')) {
      return { valid: false, reason: 'MALFORMED_DOMAIN' };
    }

    // CRITICAL SAFETY CHECK: Shared hosting domains must NEVER be blocked as an entire domain
    if (SHARED_DOMAINS.has(cleanDomain)) {
      return { valid: false, reason: 'SHARED_DOMAIN_WHOLE_BLOCK_PROHIBITED' };
    }

    const id = hashIndicatorToId('DOMAIN', cleanDomain);
    return {
      valid: true,
      id,
      type: 'DOMAIN',
      cleanValue: cleanDomain,
      threatType,
      severity,
      confidence,
      sourceName,
      description: indicator.description || `Verified ${threatType} domain (${sourceName})`
    };
  }

  if (rawType === 'URL') {
    let cleanUrl = rawValue.trim();
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      return { valid: false, reason: 'UNSUPPORTED_URL_SCHEME' };
    }

    try {
      const parsed = new URL(cleanUrl);
      const host = parsed.hostname.toLowerCase();

      // If URL is on a shared domain, ensure it has a specific path
      if (SHARED_DOMAINS.has(host) && (parsed.pathname === '/' || !parsed.pathname)) {
        return { valid: false, reason: 'SHARED_DOMAIN_ROOT_URL_PROHIBITED' };
      }

      const id = hashIndicatorToId('URL', cleanUrl);
      return {
        valid: true,
        id,
        type: 'URL',
        cleanValue: cleanUrl,
        threatType,
        severity,
        confidence,
        sourceName,
        description: indicator.description || `Verified ${threatType} URL (${sourceName})`
      };
    } catch (e) {
      return { valid: false, reason: 'MALFORMED_URL' };
    }
  }

  if (rawType === 'IP') {
    let cleanIp = rawValue.replace(/^https?:\/\//i, '').split('/')[0].trim();
    const hostPart = cleanIp.split(':')[0];

    // Basic IPv4 check
    const parts = hostPart.split('.');
    if (parts.length !== 4 || !parts.every(p => /^\d+$/.test(p) && parseInt(p, 10) >= 0 && parseInt(p, 10) <= 255)) {
      return { valid: false, reason: 'MALFORMED_IPV4' };
    }

    // SSRF / Private IP protection
    const firstOctet = parseInt(parts[0], 10);
    const secondOctet = parseInt(parts[1], 10);
    if (firstOctet === 127 || firstOctet === 10 || (firstOctet === 172 && secondOctet >= 16 && secondOctet <= 31) || (firstOctet === 192 && secondOctet === 168) || (firstOctet === 169 && secondOctet === 254)) {
      return { valid: false, reason: 'PRIVATE_OR_LOOPBACK_IP_PROHIBITED' };
    }

    const id = hashIndicatorToId('IP', cleanIp);
    return {
      valid: true,
      id,
      type: 'IP',
      cleanValue: cleanIp,
      threatType,
      severity,
      confidence,
      sourceName,
      description: indicator.description || `Verified ${threatType} IP (${sourceName})`
    };
  }

  return { valid: false, reason: 'UNKNOWN_ERROR' };
}

/**
 * Builds a Chromium declarativeNetRequest rule for a validated indicator
 */
function createDNRRule(validated, extensionBaseUrl = 'chrome-extension://cyberraksha/') {
  // Ensure extensionBaseUrl ends with /
  const base = extensionBaseUrl.endsWith('/') ? extensionBaseUrl : `${extensionBaseUrl}/`;

  let regexStr;
  if (validated.type === 'DOMAIN') {
    // Matches http:// or https://, optional subdomain prefix, the domain, optional port, and any path
    regexStr = `^https?://([^/]*\\.)?${escapeRegex(validated.cleanValue)}(:\\d+)?(/.*)?$`;
  } else if (validated.type === 'URL') {
    // Exact or prefix URL match
    const urlObj = new URL(validated.cleanValue);
    const host = urlObj.hostname;
    const pathAndQuery = urlObj.pathname + urlObj.search;
    regexStr = `^https?://([^/]*\\.)?${escapeRegex(host)}(:\\d+)?${escapeRegex(pathAndQuery)}.*$`;
  } else if (validated.type === 'IP') {
    // Matches the IP address with optional port and any path
    const hasPort = validated.cleanValue.includes(':');
    if (hasPort) {
      regexStr = `^https?://${escapeRegex(validated.cleanValue)}(/.*)?$`;
    } else {
      regexStr = `^https?://${escapeRegex(validated.cleanValue)}(:\\d+)?(/.*)?$`;
    }
  }

  return {
    id: validated.id,
    priority: 1,
    action: {
      type: 'redirect',
      redirect: {
        regexSubstitution: `${base}warning.html?url=\\0&ruleId=${validated.id}&source=DNR&class=${encodeURIComponent(validated.threatType)}&level=${encodeURIComponent(validated.severity)}`
      }
    },
    condition: {
      regexFilter: regexStr,
      resourceTypes: ['main_frame']
    }
  };
}

/**
 * Creates a high-priority session allow rule permitting a user to bypass a blocked site
 */
function createOverrideAllowRule(domainOrUrl, overrideId = 999001) {
  let cleanDomain = domainOrUrl.toLowerCase().trim();
  if (cleanDomain.startsWith('http://') || cleanDomain.startsWith('https://')) {
    try {
      cleanDomain = new URL(cleanDomain).hostname;
    } catch (e) {
      cleanDomain = cleanDomain.replace(/^https?:\/\//i, '').split('/')[0];
    }
  } else {
    cleanDomain = cleanDomain.split('/')[0].split(':')[0];
  }

  return {
    id: overrideId,
    priority: 100, // Preempts priority 1 block rules
    action: { type: 'allow' },
    condition: {
      urlFilter: `||${cleanDomain}^`,
      resourceTypes: ['main_frame']
    }
  };
}

/**
 * Calculates rule diffs (additions and removals) between currently installed
 * declarativeNetRequest rules and incoming verified threat indicators.
 */
function syncRulesDelta(currentRules, incomingIndicators, extensionBaseUrl = 'chrome-extension://cyberraksha/', maxRules = MAX_DYNAMIC_RULES) {
  const currentRuleIds = new Set((currentRules || []).map(r => r.id));
  const seenRuleIds = new Set();
  const addRules = [];
  const metadataMap = {};

  let validCount = 0;
  let rejectedCount = 0;

  for (const item of (incomingIndicators || [])) {
    const validated = validateIndicator(item);
    if (!validated.valid) {
      rejectedCount++;
      continue;
    }

    validCount++;

    // Prevent duplicates in same sync batch
    if (seenRuleIds.has(validated.id)) {
      continue;
    }
    seenRuleIds.add(validated.id);

    // Enforce rule limit cap
    if (addRules.length >= maxRules) {
      break;
    }

    const dnrRule = createDNRRule(validated, extensionBaseUrl);
    addRules.push(dnrRule);

    metadataMap[validated.id] = {
      indicator_type: validated.type,
      indicator_value: validated.cleanValue,
      threat_type: validated.threatType,
      severity: validated.severity,
      confidence_score: validated.confidence,
      source_name: validated.sourceName,
      description: validated.description,
      synced_at: new Date().toISOString()
    };
  }

  // Remove rules that are no longer in the active incoming list
  const removeRuleIds = [];
  for (const existingId of currentRuleIds) {
    if (!seenRuleIds.has(existingId)) {
      removeRuleIds.push(existingId);
    }
  }

  // Also include IDs being re-added in removeRuleIds as required by Chrome updateDynamicRules
  const allRemoveIds = Array.from(new Set([...removeRuleIds, ...addRules.map(r => r.id)]));

  return {
    addRules,
    removeRuleIds: allRemoveIds,
    metadataMap,
    stats: {
      totalIncoming: (incomingIndicators || []).length,
      validCount,
      rejectedCount,
      addCount: addRules.length,
      removeCount: removeRuleIds.length
    }
  };
}

/**
 * Sensitive query parameter names that must be redacted for privacy and security
 */
const SENSITIVE_QUERY_PARAMS = new Set([
  'password', 'passwd', 'pass', 'pwd',
  'token', 'access_token', 'id_token', 'refresh_token', 'bearer',
  'secret', 'client_secret', 'api_key', 'apikey', 'key',
  'auth', 'authorization', 'code', 'session', 'session_id',
  'sid', 'state', 'otp', 'pin', 'ssn', 'cvv'
]);

/**
 * Strips sensitive authentication and token query parameters from URLs
 */
function sanitizeUrl(urlStr) {
  if (!urlStr || typeof urlStr !== 'string') return '';
  try {
    const parsed = new URL(urlStr);
    let changed = false;
    for (const key of Array.from(parsed.searchParams.keys())) {
      if (SENSITIVE_QUERY_PARAMS.has(key.toLowerCase())) {
        parsed.searchParams.set(key, '[REDACTED]');
        changed = true;
      }
    }
    if (parsed.hash && /token|password|auth|secret|key/i.test(parsed.hash)) {
      parsed.hash = '#[REDACTED]';
    }
    return parsed.toString();
  } catch (e) {
    return urlStr;
  }
}

/**
 * Verified infrastructure and popular safe domains to avoid unnecessary blocking
 */
const KNOWN_SAFE_DOMAINS = new Set([
  'google.com', 'www.google.com', 'accounts.google.com', 'mail.google.com',
  'microsoft.com', 'www.microsoft.com', 'login.microsoftonline.com',
  'apple.com', 'www.apple.com',
  'github.com', 'www.github.com', 'api.github.com',
  'wikipedia.org', 'en.wikipedia.org',
  'youtube.com', 'www.youtube.com',
  'vercel.app', 'onrender.com', 'neon.tech',
  'cyberraksha-backend.onrender.com', 'frontend-lilac-nu-50.vercel.app',
  'localhost', '127.0.0.1'
]);

/**
 * Checks if a hostname belongs to a known safe infrastructure domain
 */
function isWhitelistedSafeDomain(hostname) {
  if (!hostname) return false;
  const host = hostname.toLowerCase().trim();
  if (KNOWN_SAFE_DOMAINS.has(host)) return true;
  for (const safe of KNOWN_SAFE_DOMAINS) {
    if (host === safe || host.endsWith('.' + safe)) return true;
  }
  return false;
}

/**
 * Creates an on-the-fly dynamic DNR rule for live navigation intercepts
 */
function createDynamicBlockRule(targetUrl, threatType = 'PHISHING', severity = 'CRITICAL', ruleId = null, extensionBaseUrl = 'chrome-extension://cyberraksha/') {
  const base = extensionBaseUrl.endsWith('/') ? extensionBaseUrl : `${extensionBaseUrl}/`;
  let cleanUrl = targetUrl.trim();
  let host = '';
  let id = ruleId;
  try {
    const parsed = new URL(cleanUrl);
    host = parsed.hostname.toLowerCase();
    if (!id) {
      id = hashIndicatorToId('URL', cleanUrl);
    }
  } catch (e) {
    host = cleanUrl.replace(/^https?:\/\//i, '').split('/')[0];
    if (!id) id = 950000 + Math.floor(Math.random() * 40000);
  }

  let regexStr;
  if (SHARED_DOMAINS.has(host)) {
    try {
      const parsed = new URL(cleanUrl);
      const pathAndQuery = parsed.pathname + (parsed.search || '');
      regexStr = `^https?://([^/]*\\.)?${escapeRegex(host)}(:\\d+)?${escapeRegex(pathAndQuery)}.*$`;
    } catch (e) {
      regexStr = `^https?://([^/]*\\.)?${escapeRegex(host)}(:\\d+)?(/.*)?$`;
    }
  } else {
    regexStr = `^https?://([^/]*\\.)?${escapeRegex(host)}(:\\d+)?(/.*)?$`;
  }

  return {
    id: id,
    priority: 10, // Preempts standard feed rules
    action: {
      type: 'redirect',
      redirect: {
        regexSubstitution: `${base}warning.html?url=\\0&ruleId=${id}&source=REALTIME_DNR&class=${encodeURIComponent(threatType)}&level=${encodeURIComponent(severity)}`
      }
    },
    condition: {
      regexFilter: regexStr,
      resourceTypes: ['main_frame']
    }
  };
}

// Export for Node.js test suites while remaining global in browser service worker
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    SHARED_DOMAINS,
    KNOWN_SAFE_DOMAINS,
    MAX_DYNAMIC_RULES,
    MIN_CONFIDENCE_THRESHOLD,
    SENSITIVE_QUERY_PARAMS,
    sanitizeUrl,
    isWhitelistedSafeDomain,
    hashIndicatorToId,
    escapeRegex,
    validateIndicator,
    createDNRRule,
    createDynamicBlockRule,
    createOverrideAllowRule,
    syncRulesDelta
  };
}

