/**
 * browser_extension/tests/verify_a1_deep_audit.js
 * In-depth technical verification script for Phase A1:
 * - Exact domain matching
 * - Subdomain matching
 * - Similar-looking domain rejection
 * - HTTP and HTTPS handling
 * - Ports, paths, query strings and fragments
 * - URL encoding and Unicode (Punycode)
 * - Shared hosting protection
 * - Expired and revoked indicators
 * - Duplicate indicators
 * - Session override priority and behavior
 * - Open redirect and scheme handling in warning interstitial logic
 */
const assert = require('assert');
const {
  SHARED_DOMAINS,
  MAX_DYNAMIC_RULES,
  MIN_CONFIDENCE_THRESHOLD,
  hashIndicatorToId,
  escapeRegex,
  validateIndicator,
  createDNRRule,
  createOverrideAllowRule,
  syncRulesDelta
} = require('../rules_manager.js');

console.log('============================================================');
console.log('PHASE A1 DEEP TECHNICAL VERIFICATION SUITE');
console.log('============================================================\n');

let passedCount = 0;
let failedCount = 0;

function runTest(testName, fn) {
  try {
    fn();
    console.log(`  [PASS] ${testName}`);
    passedCount++;
  } catch (err) {
    console.error(`  [FAIL] ${testName}: ${err.message}`);
    failedCount++;
  }
}

// ---------------------------------------------------------------------------
// 1. Exact Domain Matching
// ---------------------------------------------------------------------------
runTest('Exact domain matching', () => {
  const indicator = {
    indicator_type: 'DOMAIN',
    indicator_value: 'malicious-portal.invalid',
    threat_type: 'PHISHING',
    severity: 'HIGH',
    confidence_score: 0.95
  };
  const val = validateIndicator(indicator);
  assert.strictEqual(val.valid, true);
  const rule = createDNRRule(val, 'chrome-extension://test/');
  const regex = new RegExp(rule.condition.regexFilter);

  assert.strictEqual(regex.test('http://malicious-portal.invalid'), true);
  assert.strictEqual(regex.test('https://malicious-portal.invalid'), true);
  assert.strictEqual(regex.test('https://malicious-portal.invalid/'), true);
  assert.strictEqual(regex.test('https://malicious-portal.invalid/login'), true);
});

// ---------------------------------------------------------------------------
// 2. Subdomain Matching
// ---------------------------------------------------------------------------
runTest('Subdomain matching against parent domain rule', () => {
  const val = validateIndicator({
    indicator_type: 'DOMAIN',
    indicator_value: 'malicious-portal.invalid',
    threat_type: 'PHISHING',
    severity: 'HIGH',
    confidence_score: 0.95
  });
  const rule = createDNRRule(val);
  const regex = new RegExp(rule.condition.regexFilter);

  assert.strictEqual(regex.test('https://sub.malicious-portal.invalid'), true);
  assert.strictEqual(regex.test('https://auth.sub.malicious-portal.invalid/pay'), true);
  assert.strictEqual(regex.test('http://level3.level2.level1.malicious-portal.invalid:8080/'), true);
});

// ---------------------------------------------------------------------------
// 3. Similar-Looking Domain Rejection (No False Positives)
// ---------------------------------------------------------------------------
runTest('Similar-looking domain rejection', () => {
  const val = validateIndicator({
    indicator_type: 'DOMAIN',
    indicator_value: 'malicious-portal.invalid',
    threat_type: 'PHISHING',
    severity: 'HIGH',
    confidence_score: 0.95
  });
  const rule = createDNRRule(val);
  const regex = new RegExp(rule.condition.regexFilter);

  // Different TLD / Country code extension
  assert.strictEqual(regex.test('https://malicious-portal.invalid.co'), false);
  assert.strictEqual(regex.test('https://malicious-portal.invalid.com'), false);

  // Prefix variations
  assert.strictEqual(regex.test('https://notmalicious-portal.invalid'), false);
  assert.strictEqual(regex.test('https://truemalicious-portal.invalid'), false);

  // Suffix variations before TLD
  assert.strictEqual(regex.test('https://malicious-portal.invalidsite.com'), false);

  // Subdomain of an entirely different domain
  assert.strictEqual(regex.test('https://malicious-portal.invalid.attacker.org'), false);
});

// ---------------------------------------------------------------------------
// 4. HTTP and HTTPS Handling
// ---------------------------------------------------------------------------
runTest('HTTP and HTTPS handling', () => {
  const val = validateIndicator({
    indicator_type: 'DOMAIN',
    indicator_value: 'phish-target.invalid',
    threat_type: 'PHISHING',
    severity: 'HIGH',
    confidence_score: 0.95
  });
  const rule = createDNRRule(val);
  const regex = new RegExp(rule.condition.regexFilter);

  assert.strictEqual(regex.test('http://phish-target.invalid/'), true);
  assert.strictEqual(regex.test('https://phish-target.invalid/'), true);
  // Non-HTTP schemes must NOT match
  assert.strictEqual(regex.test('ftp://phish-target.invalid/'), false);
  assert.strictEqual(regex.test('file:///phish-target.invalid/'), false);
  assert.strictEqual(regex.test('ws://phish-target.invalid/'), false);
});

// ---------------------------------------------------------------------------
// 5. Ports, Paths, Query Strings and Fragments
// ---------------------------------------------------------------------------
runTest('Ports, paths, query strings and fragments handling', () => {
  const val = validateIndicator({
    indicator_type: 'DOMAIN',
    indicator_value: 'evil-host.invalid',
    threat_type: 'MALWARE_DOWNLOAD',
    severity: 'CRITICAL',
    confidence_score: 0.99
  });
  const rule = createDNRRule(val);
  const regex = new RegExp(rule.condition.regexFilter);

  assert.strictEqual(regex.test('https://evil-host.invalid:8443/api/v1/payload'), true);
  assert.strictEqual(regex.test('http://evil-host.invalid:80/download?id=1234&token=xyz'), true);
  assert.strictEqual(regex.test('https://evil-host.invalid:3000/app/#/login'), true);
});

// ---------------------------------------------------------------------------
// 6. URL Encoding and Unicode / IDN (Punycode) Handling
// ---------------------------------------------------------------------------
runTest('URL encoding and Unicode / IDN handling', () => {
  // Test encoded characters in path
  const urlVal = validateIndicator({
    indicator_type: 'URL',
    indicator_value: 'https://evil-host.invalid/path%20with%20spaces/payload.exe',
    threat_type: 'MALWARE_DOWNLOAD',
    severity: 'CRITICAL',
    confidence_score: 0.95
  });
  assert.strictEqual(urlVal.valid, true);
  const rule = createDNRRule(urlVal);
  const regex = new RegExp(rule.condition.regexFilter);
  assert.strictEqual(regex.test('https://evil-host.invalid/path%20with%20spaces/payload.exe'), true);

  // Test Punycode domain (xn--...)
  const punyVal = validateIndicator({
    indicator_type: 'DOMAIN',
    indicator_value: 'xn--sbi-kyc-update-123.invalid',
    threat_type: 'PHISHING',
    severity: 'HIGH',
    confidence_score: 0.90
  });
  assert.strictEqual(punyVal.valid, true);
  const punyRule = createDNRRule(punyVal);
  const punyRegex = new RegExp(punyRule.condition.regexFilter);
  assert.strictEqual(punyRegex.test('https://xn--sbi-kyc-update-123.invalid/login'), true);
  assert.strictEqual(punyRegex.test('https://not-xn--sbi-kyc-update-123.invalid/login'), false);
});

// ---------------------------------------------------------------------------
// 7. Shared Hosting Protection
// ---------------------------------------------------------------------------
runTest('Shared hosting protection', () => {
  // 1. Naked shared domain must be rejected
  const nakedGithub = validateIndicator({
    indicator_type: 'DOMAIN',
    indicator_value: 'github.com',
    threat_type: 'PHISHING',
    severity: 'CRITICAL',
    confidence_score: 0.99
  });
  assert.strictEqual(nakedGithub.valid, false);
  assert.strictEqual(nakedGithub.reason, 'SHARED_DOMAIN_WHOLE_BLOCK_PROHIBITED');

  const nakedGoogleDocs = validateIndicator({
    indicator_type: 'DOMAIN',
    indicator_value: 'docs.google.com',
    threat_type: 'PHISHING',
    severity: 'CRITICAL',
    confidence_score: 0.99
  });
  assert.strictEqual(nakedGoogleDocs.valid, false);

  // 2. Root URL on shared domain must be rejected
  const rootVercel = validateIndicator({
    indicator_type: 'URL',
    indicator_value: 'https://vercel.app/',
    threat_type: 'PHISHING',
    severity: 'HIGH',
    confidence_score: 0.90
  });
  assert.strictEqual(rootVercel.valid, false);
  assert.strictEqual(rootVercel.reason, 'SHARED_DOMAIN_ROOT_URL_PROHIBITED');

  // 3. Deep subpath URL on shared domain is PERMITTED
  const deepGithub = validateIndicator({
    indicator_type: 'URL',
    indicator_value: 'https://github.com/phish-actor/fake-sbi-portal/login.html',
    threat_type: 'PHISHING',
    severity: 'HIGH',
    confidence_score: 0.95
  });
  assert.strictEqual(deepGithub.valid, true);
  const deepRule = createDNRRule(deepGithub);
  const deepRegex = new RegExp(deepRule.condition.regexFilter);
  assert.strictEqual(deepRegex.test('https://github.com/phish-actor/fake-sbi-portal/login.html'), true);
  // Legitimate GitHub pages must NOT match
  assert.strictEqual(deepRegex.test('https://github.com/torvalds/linux'), false);
  assert.strictEqual(deepRegex.test('https://github.com/'), false);
});

// ---------------------------------------------------------------------------
// 8. Expired and Revoked Indicators
// ---------------------------------------------------------------------------
runTest('Expired and revoked indicators removal in syncRulesDelta', () => {
  const currentRules = [
    { id: 1001, condition: { regexFilter: 'rule1' } },
    { id: 1002, condition: { regexFilter: 'rule2' } },
    { id: 1003, condition: { regexFilter: 'rule3' } }
  ];

  // Indicator 1001 is active, 1002 is inactive (revoked), 1003 is omitted (expired)
  const incoming = [
    {
      indicator_type: 'DOMAIN',
      indicator_value: 'site1.invalid',
      threat_type: 'PHISHING',
      severity: 'HIGH',
      confidence_score: 0.9,
      is_active: true
    },
    {
      indicator_type: 'DOMAIN',
      indicator_value: 'site2.invalid',
      threat_type: 'PHISHING',
      severity: 'HIGH',
      confidence_score: 0.9,
      is_active: false // Revoked
    }
  ];

  const delta = syncRulesDelta(currentRules, incoming);
  // Rule 1002 (inactive) and 1003 (expired/omitted) must be in removeRuleIds
  assert.strictEqual(delta.removeRuleIds.includes(1002), true);
  assert.strictEqual(delta.removeRuleIds.includes(1003), true);
});

// ---------------------------------------------------------------------------
// 9. Duplicate Indicators
// ---------------------------------------------------------------------------
runTest('Duplicate indicators deduplication in sync feed', () => {
  const incoming = [
    { indicator_type: 'DOMAIN', indicator_value: 'dup-site.invalid', threat_type: 'PHISHING', severity: 'HIGH', confidence_score: 0.9 },
    { indicator_type: 'DOMAIN', indicator_value: 'dup-site.invalid', threat_type: 'PHISHING', severity: 'HIGH', confidence_score: 0.9 },
    { indicator_type: 'DOMAIN', indicator_value: 'DUP-SITE.INVALID', threat_type: 'PHISHING', severity: 'HIGH', confidence_score: 0.9 }
  ];

  const delta = syncRulesDelta([], incoming);
  assert.strictEqual(delta.addRules.length, 1);
});

// ---------------------------------------------------------------------------
// 10. Session Override Priority and Behavior
// ---------------------------------------------------------------------------
runTest('Session override rule priority and structure', () => {
  const allowRule = createOverrideAllowRule('https://suspicious-test.invalid/login');
  assert.strictEqual(allowRule.priority, 100); // Preempts block priority (1)
  assert.strictEqual(allowRule.action.type, 'allow');
  assert.strictEqual(allowRule.condition.urlFilter, '||suspicious-test.invalid^');
  assert.deepStrictEqual(allowRule.condition.resourceTypes, ['main_frame']);
});

console.log(`\n============================================================`);
console.log(`DEEP VERIFICATION COMPLETED: ${passedCount} PASSED / ${failedCount} FAILED`);
console.log(`============================================================`);

if (failedCount > 0) {
  process.exit(1);
}

