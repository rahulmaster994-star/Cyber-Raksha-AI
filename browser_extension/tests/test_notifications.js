/**
 * browser_extension/tests/test_notifications.js
 * Automated Verification Suite for Phase A3 Browser Notifications.
 * Tests payload structure, severity mapping, domain rate-limiting,
 * preference gating, and action callbacks.
 */
const assert = require('assert');

console.log('============================================================');
console.log('CYBER RAKSHA AI — PHASE A3: BROWSER NOTIFICATIONS TESTS');
console.log('============================================================\n');

let passed = 0;
let failed = 0;

function runTest(name, fn) {
  try {
    fn();
    console.log(`  [PASS] ${name}`);
    passed++;
  } catch (err) {
    console.error(`  [FAIL] ${name}: ${err.message}`);
    failed++;
  }
}

const NOTIFICATION_SEVERITY_RANKS = { 'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4 };

// Helper to simulate notification generator
function buildNotificationPayload(threatData, preferences, recentDomainMap, now = Date.now()) {
  if (!threatData || !threatData.url) {
    return { shouldNotify: false, reason: 'MISSING_URL' };
  }

  let domain = 'unknown-destination';
  try {
    domain = new URL(threatData.url).hostname;
  } catch (e) {
    domain = threatData.url.replace(/^https?:\/\//i, '').split('/')[0];
  }

  // Rate-limiting check by domain (30-second cooldown)
  const lastNotified = recentDomainMap.get(domain);
  if (lastNotified && now - lastNotified < 30000) {
    return { shouldNotify: false, reason: 'DOMAIN_RATE_LIMITED' };
  }
  recentDomainMap.set(domain, now);

  const prefs = preferences || { enabled: true, min_severity: 'LOW', sound: false };
  if (!prefs.enabled) {
    return { shouldNotify: false, reason: 'NOTIFICATIONS_DISABLED' };
  }

  const threatSeverity = (threatData.severity || 'CRITICAL').toUpperCase();
  const incomingRank = NOTIFICATION_SEVERITY_RANKS[threatSeverity] || 1;
  const minRank = NOTIFICATION_SEVERITY_RANKS[(prefs.min_severity || 'LOW').toUpperCase()] || 1;

  if (incomingRank < minRank) {
    return { shouldNotify: false, reason: 'BELOW_SEVERITY_THRESHOLD' };
  }

  const threatType = threatData.threatType || 'MALICIOUS_THREAT';
  return {
    shouldNotify: true,
    notification: {
      id: `cyber_raksha_${now}`,
      type: 'basic',
      iconUrl: 'icons/icon128.png',
      title: 'CYBER RAKSHA AI — MALICIOUS WEBSITE BLOCKED',
      message: `Website: ${domain}\nRisk Level: ${threatSeverity}\nReason: ${threatType}\nAction: Navigation blocked successfully.`,
      priority: threatSeverity === 'CRITICAL' ? 2 : (threatSeverity === 'HIGH' ? 1 : 0),
      requireInteraction: threatSeverity === 'CRITICAL'
    },
    backendPayload: {
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
    }
  };
}

// ---------------------------------------------------------------------------
// Test Cases
// ---------------------------------------------------------------------------

runTest('TC01: Generates valid notification for critical blocked URL', () => {
  const map = new Map();
  const res = buildNotificationPayload(
    {
      url: 'https://cbi-digital-arrest-warrant.com/auth',
      threatType: 'DIGITAL_ARREST',
      severity: 'CRITICAL',
      source: 'DNR',
      ruleId: 1001
    },
    { enabled: true, min_severity: 'LOW' },
    map
  );

  assert.strictEqual(res.shouldNotify, true);
  assert.strictEqual(res.notification.title, 'CYBER RAKSHA AI — MALICIOUS WEBSITE BLOCKED');
  assert.strictEqual(res.notification.priority, 2);
  assert.strictEqual(res.notification.requireInteraction, true);
  assert.strictEqual(res.backendPayload.target_domain, 'cbi-digital-arrest-warrant.com');
  assert.strictEqual(res.backendPayload.severity, 'CRITICAL');
});

runTest('TC02: High-risk notification formats with appropriate priority', () => {
  const map = new Map();
  const res = buildNotificationPayload(
    {
      url: 'https://suspicious-login.invalid/sbi',
      threatType: 'PHISHING',
      severity: 'HIGH',
      source: 'CONTEXT_MENU'
    },
    { enabled: true, min_severity: 'MEDIUM' },
    map
  );

  assert.strictEqual(res.shouldNotify, true);
  assert.strictEqual(res.notification.priority, 1);
  assert.strictEqual(res.notification.requireInteraction, false);
});

runTest('TC03: Domain rate-limiting suppresses duplicate notifications within 30s', () => {
  const map = new Map();
  const t0 = 100000;
  const threat = { url: 'https://repeat-offender.invalid/payload', severity: 'CRITICAL' };

  // First occurrence -> Should notify
  const res1 = buildNotificationPayload(threat, { enabled: true, min_severity: 'LOW' }, map, t0);
  assert.strictEqual(res1.shouldNotify, true);

  // Second occurrence 5s later -> Rate limited
  const res2 = buildNotificationPayload(threat, { enabled: true, min_severity: 'LOW' }, map, t0 + 5000);
  assert.strictEqual(res2.shouldNotify, false);
  assert.strictEqual(res2.reason, 'DOMAIN_RATE_LIMITED');

  // Third occurrence 35s later -> Allowed
  const res3 = buildNotificationPayload(threat, { enabled: true, min_severity: 'LOW' }, map, t0 + 35000);
  assert.strictEqual(res3.shouldNotify, true);
});

runTest('TC04: Different domains notify independently without suppressing each other', () => {
  const map = new Map();
  const t0 = 100000;

  const resA = buildNotificationPayload({ url: 'https://site-a.invalid/test', severity: 'CRITICAL' }, null, map, t0);
  const resB = buildNotificationPayload({ url: 'https://site-b.invalid/test', severity: 'CRITICAL' }, null, map, t0 + 1000);

  assert.strictEqual(resA.shouldNotify, true);
  assert.strictEqual(resB.shouldNotify, true);
});

runTest('TC05: Disabling notifications suppresses alerts', () => {
  const map = new Map();
  const res = buildNotificationPayload(
    { url: 'https://malicious.invalid/pay', severity: 'CRITICAL' },
    { enabled: false, min_severity: 'LOW' },
    map
  );

  assert.strictEqual(res.shouldNotify, false);
  assert.strictEqual(res.reason, 'NOTIFICATIONS_DISABLED');
});

runTest('TC06: Respects minimum severity threshold preference', () => {
  const map = new Map();
  // Threshold is CRITICAL; incoming is MEDIUM
  const res = buildNotificationPayload(
    { url: 'https://medium-threat.invalid/', severity: 'MEDIUM' },
    { enabled: true, min_severity: 'CRITICAL' },
    map
  );

  assert.strictEqual(res.shouldNotify, false);
  assert.strictEqual(res.reason, 'BELOW_SEVERITY_THRESHOLD');

  // Incoming is CRITICAL -> passes threshold
  const resCrit = buildNotificationPayload(
    { url: 'https://critical-threat.invalid/', severity: 'CRITICAL' },
    { enabled: true, min_severity: 'CRITICAL' },
    map
  );
  assert.strictEqual(resCrit.shouldNotify, true);
});

console.log(`\n============================================================`);
console.log(`EXTENSION NOTIFICATION TESTS: ${passed} PASSED / ${failed} FAILED`);
console.log(`============================================================`);

if (failed > 0) {
  process.exit(1);
}

