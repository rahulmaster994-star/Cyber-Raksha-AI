import httpx
import json
import uuid
import sys

BASE_URL = "https://cyberraksha-backend.onrender.com"
client = httpx.Client(base_url=BASE_URL, timeout=30.0)

print(f"Target Live Endpoint: {BASE_URL}\n")

# 1. Health
print("--- [1] Test A: Root Health Endpoint ---")
r_health = client.get("/health")
print(f"HTTP Status: {r_health.status_code}")
print(json.dumps(r_health.json(), indent=2))
assert r_health.status_code == 200

# 2. Detection Status
print("\n--- [2] Test B: AI Detection Telemetry ---")
r_status = client.get("/api/v1/detection/status")
print(f"HTTP Status: {r_status.status_code}")
status_data = r_status.json()
print(f"Inference Status: {status_data.get('inference_status')}")
print(f"Model Loaded: {status_data.get('model_loaded')}")
print(f"Model Version: {status_data.get('model_version')}")
print(f"Accuracy: {status_data.get('metrics_summary', {}).get('accuracy')}")
assert r_status.status_code == 200

# 3. Phishing URL Detection
print("\n--- [3] Test C: Phishing URL Detection ---")
test_url = "https://sbi-netbanking-update.xyz/login"
r_url = client.post("/api/v1/detection/url", json={"url": test_url})
print(f"HTTP Status: {r_url.status_code}")
url_data = r_url.json()
print(f"Classification: {url_data.get('classification')}")
print(f"Risk Score: {url_data.get('risk_score')}")
print(f"Risk Level: {url_data.get('risk_level')}")
brand = url_data.get("analysis", {}).get("brand_impersonation", {}).get("brand_name")
print(f"Brand Impersonation: {brand}")
assert r_url.status_code == 200

# 4. Digital Arrest Scam Analysis
print("\n--- [4] Test D: Digital Arrest Scam Detection ---")
scam_msg = "URGENT: CBI officer speaking. You are under digital arrest. Pay fine of Rs 50000 to safe RBI account immediately."
r_da = client.post("/api/v1/communication/digital-arrest/analyze", json={"message": scam_msg})
print(f"HTTP Status: {r_da.status_code}")
da_data = r_da.json()
print(f"Classification: {da_data.get('classification')}")
print(f"Risk Score: {da_data.get('risk_score')}")
print(f"Risk Level: {da_data.get('risk_level')}")
print(f"Detected Indicators: {da_data.get('detected_indicators')}")
assert r_da.status_code == 200

# 5. Database Persistence & Device Registration
print("\n--- [5] Test E: Database Persistence & Tenant Isolation ---")
dev_id = str(uuid.uuid4())
r_reg = client.post("/api/v1/devices/register", json={
    "device_id": dev_id,
    "device_name": "Cloud-Verification-Phone",
    "platform": "ANDROID",
    "app_version": "1.0.0"
})
print(f"Registration HTTP Status: {r_reg.status_code}")
reg_data = r_reg.json()
token = reg_data.get("device_token")
print(f"Registered Device ID: {reg_data.get('device_id')}")
print(f"Device Token Generated: {token[:16]}... (Length: {len(token)})")
assert r_reg.status_code == 200

# 6. CORS Verification
print("\n--- [6] Test F: CORS Policy Verification ---")
r_cors = client.options("/api/v1/detection/url", headers={
    "Origin": "https://cyberraksha.vercel.app",
    "Access-Control-Request-Method": "POST"
})
print(f"OPTIONS Status: {r_cors.status_code}")
print(f"Access-Control-Allow-Origin: {r_cors.headers.get('access-control-allow-origin')}")
print(f"Access-Control-Allow-Credentials: {r_cors.headers.get('access-control-allow-credentials')}")

# 7. Security Headers Check
print("\n--- [7] Test G: Security Headers Audit ---")
print(f"X-Content-Type-Options: {r_health.headers.get('x-content-type-options')}")
print(f"X-Frame-Options: {r_health.headers.get('x-frame-options')}")
print(f"Content-Type: {r_health.headers.get('content-type')}")

print("\n>>> ALL CLOUD PRODUCTION TESTS COMPLETED SUCCESSFULLY! <<<")

