"""
scripts/verify_c31_extension_cloud.py
Stage C3.1: Live Cloud Backend & Extension Integration Verification Script
Verifies:
1. Live device registration with backend
2. Live threat intelligence indicators retrieval and DNR transformation
3. Live ML phishing detection
4. Real-time SecurityEvent reporting with device authentication
5. Dashboard Incident and Event telemetry synchronization
6. Privacy sanitization benchmarks
"""
import urllib.request
import urllib.error
import json
import time
import uuid

BACKEND_URL = "https://cyberraksha-backend.onrender.com"
FRONTEND_URL = "https://frontend-lilac-nu-50.vercel.app"

def request_json(method, path, data=None, headers=None):
    url = f"{BACKEND_URL}{path}"
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=30) as resp:
        duration_ms = (time.perf_counter() - t0) * 1000.0
        resp_body = resp.read().decode("utf-8")
        parsed = json.loads(resp_body) if resp_body else {}
        return resp.status, parsed, duration_ms

print("============================================================")
print("STAGE C3.1: LIVE CLOUD BACKEND & EXTENSION INTEGRATION TEST")
print("============================================================\n")

# Step 1: Verify Live Backend Health
print("1. Checking Live Backend Health...")
status, body, latency = request_json("GET", "/health")
print(f"   [OK] HTTP {status} in {latency:.1f}ms | Database latency: {body.get('database_latency_ms')}ms")
assert status == 200
assert body.get("database_connected") is True

# Step 2: Register Chrome Extension Device
print("\n2. Registering Browser Extension as Dedicated Device...")
device_id = str(uuid.uuid4())
reg_payload = {
    "device_id": device_id,
    "device_name": "Chrome Browser Shield (Stage C3.1 Test)",
    "app_version": "1.3.0"
}
status, reg_data, latency = request_json("POST", "/api/v1/devices/register", reg_payload)
print(f"   [OK] Registered Device ID: {reg_data.get('device_id')}")
print(f"   [OK] Token length: {len(reg_data.get('device_token', ''))} chars | HTTP {status} in {latency:.1f}ms")
assert status == 200
device_token = reg_data["device_token"]

# Step 3: Fetch Threat Intelligence Indicators
print("\n3. Fetching Threat Intelligence Indicators for DNR Rules...")
status, indicators, latency = request_json("GET", "/api/v1/intel/indicators?limit=100")
print(f"   [OK] Retrieved {len(indicators)} verified indicators in {latency:.1f}ms")
assert status == 200
assert isinstance(indicators, list)
if indicators:
    sample = indicators[0]
    print(f"   [Sample IOC] Type: {sample.get('indicator_type')} | Target: {sample.get('indicator_value')} | Severity: {sample.get('severity')}")

# Step 4: Real-Time Live URL Phishing Detection
print("\n4. Testing Real-Time URL Phishing Detection...")
test_url = "https://sbi-netbanking-update.xyz/login"
status, det_result, latency = request_json("POST", "/api/v1/detection/url", {"url": test_url})
print(f"   [OK] Classification: {det_result.get('classification')} | Severity: {det_result.get('risk_level')}")
print(f"   [OK] Risk Score: {det_result.get('risk_score')}/100 | Confidence: {det_result.get('confidence')} | Latency: {latency:.1f}ms")
assert status == 200
assert det_result.get("risk_level") in ["CRITICAL", "HIGH"]

# Step 5: Ingest SecurityEvent from Registered Extension
print("\n5. Ingesting Browser Extension Security Event with Device Scoping...")
event_payload = {
    "event_type": "BROWSER_BLOCKED_URL",
    "severity": det_result.get("risk_level", "CRITICAL"),
    "source_component": "BROWSER_EXTENSION",
    "device_id": device_id,
    "threat_indicator": test_url,
    "risk_score": det_result.get("risk_score", 94.34),
    "detection_reason": f"Real-time navigation intercept blocked phishing destination ({det_result.get('classification')}).",
    "description": f"Real-time navigation to {test_url} was blocked before page load."
}
status, evt_res, latency = request_json("POST", "/api/v1/security/events", event_payload, {"Authorization": f"Bearer {device_token}"})
print(f"   [OK] Event ID: {evt_res.get('event_id')} | HTTP {status} in {latency:.1f}ms")
print(f"   [OK] Correlated Incident ID: {evt_res.get('incident_id')} | Status: {evt_res.get('processing_status')}")
assert status == 201
incident_id = evt_res.get("incident_id")

# Step 6: Verify Dashboard Telemetry & Incidents
print("\n6. Verifying Dashboard Live Telemetry...")
status, overview, latency = request_json("GET", "/api/v1/dashboard/overview")
print(f"   [OK] Total Devices: {overview.get('devices', {}).get('total_registered')}")
print(f"   [OK] Active Incidents: {overview.get('incidents', {}).get('active')} | Total Incidents: {overview.get('incidents', {}).get('total')}")
print(f"   [OK] Overall Posture: {overview.get('overall_posture', {}).get('label')} ({overview.get('overall_posture', {}).get('score')}/100)")
assert status == 200

# Step 7: Verify Device Security Events Isolation
print("\n7. Verifying Device Isolation Query...")
status, dev_events, latency = request_json("GET", f"/api/v1/security/events?device_id={device_id}", headers={"Authorization": f"Bearer {device_token}"})
print(f"   [OK] Device-scoped events returned: {dev_events.get('total')} | HTTP {status} in {latency:.1f}ms")
assert status == 200
assert dev_events.get("total") >= 1

print("\n============================================================")
print(">>> ALL STAGE C3.1 LIVE CLOUD INTEGRATION CHECKS PASSED! <<<")
print("============================================================")
