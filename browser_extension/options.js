// options.js — Handles extension options persistence & threat feed telemetry
document.addEventListener('DOMContentLoaded', async () => {
  const input = document.getElementById('apiUrl');
  const notifEnabled = document.getElementById('notifEnabled');
  const notifMinSeverity = document.getElementById('notifMinSeverity');
  const notifSound = document.getElementById('notifSound');

  try {
    const stored = await chrome.storage.sync.get(['apiUrl']);
    input.value = stored.apiUrl || 'https://cyberraksha-backend.onrender.com';
  } catch (e) {
    input.value = 'https://cyberraksha-backend.onrender.com';
  }

  // Load Phase A3 notification preferences
  try {
    const local = await chrome.storage.local.get(['notificationPreferences']);
    const prefs = local.notificationPreferences || {
      enabled: true,
      min_severity: 'LOW',
      sound: false
    };
    notifEnabled.checked = prefs.enabled !== false;
    notifMinSeverity.value = prefs.min_severity || 'LOW';
    notifSound.checked = !!prefs.sound;
  } catch (e) {
    // Defaults
  }

  loadTelemetry();

  document.getElementById('btnSave').addEventListener('click', async () => {
    const val = input.value.trim().replace(/\/+$/, '');
    await chrome.storage.sync.set({ apiUrl: val });

    // Save notification preferences
    const prefs = {
      enabled: notifEnabled.checked,
      min_severity: notifMinSeverity.value,
      sound: notifSound.checked
    };
    await chrome.storage.local.set({ notificationPreferences: prefs });

    // Also sync to backend API if reachable
    try {
      await fetch(`${val}/api/v1/notifications/preferences`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          browser_notifications_enabled: prefs.enabled,
          min_severity: prefs.min_severity,
          sound_enabled: prefs.sound
        })
      });
    } catch (_) {}

    showMsg('Settings and notification preferences saved successfully.', '#34d399');
  });

  document.getElementById('btnTest').addEventListener('click', async () => {
    const val = input.value.trim().replace(/\/+$/, '');
    showMsg('Testing connection to backend...', '#00f0ff');
    try {
      const res = await fetch(`${val}/api/health`);
      if (res.ok) {
        showMsg('Connection SUCCESSFUL: Cyber Raksha API is online and operational.', '#34d399');
      } else {
        showMsg(`Connection returned HTTP ${res.status}. Check server logs.`, '#fbbf24');
      }
    } catch (err) {
      showMsg(`Connection FAILED: Cannot reach ${val}. Ensure the FastAPI server is running.`, '#f87171');
    }
  });

  document.getElementById('btnSync').addEventListener('click', async () => {
    const btn = document.getElementById('btnSync');
    btn.disabled = true;
    showMsg('Synchronizing threat intelligence rules with backend...', '#00f0ff');

    chrome.runtime.sendMessage({ action: 'SYNC_THREAT_INTEL' }, (res) => {
      btn.disabled = false;
      if (res && res.success) {
        showMsg(`Synchronization COMPLETE: Installed ${res.count} active blocking rules.`, '#34d399');
      } else {
        showMsg(`Synchronization OFFLINE: ${res?.error || 'Using previously cached rules.'}`, '#fbbf24');
      }
      loadTelemetry();
    });
  });
});

function loadTelemetry() {
  chrome.runtime.sendMessage({ action: 'GET_PROTECTION_STATUS' }, (res) => {
    if (chrome.runtime.lastError || !res) return;

    document.getElementById('rulesCount').innerText = `${res.activeRulesCount} Rules`;
    document.getElementById('overridesCount').innerText = `${res.sessionOverridesCount} Overrides`;
    document.getElementById('lastSync').innerText = res.lastSyncTime ? new Date(res.lastSyncTime).toLocaleString() : 'Never';

    const syncEl = document.getElementById('syncStatus');
    syncEl.innerText = res.lastSyncStatus;
    if (res.lastSyncStatus === 'SUCCESS') {
      syncEl.style.color = '#34d399';
    } else if (res.lastSyncStatus === 'OFFLINE_FALLBACK') {
      syncEl.style.color = '#fbbf24';
    } else {
      syncEl.style.color = '#f87171';
    }
  });
}

function showMsg(text, color) {
  const el = document.getElementById('statusMsg');
  el.innerText = text;
  el.style.color = color;
}
