import urllib.request
import json
import uuid

base_url = 'https://cyberraksha-backend.onrender.com'
headers = {
    'User-Agent': 'CyberRaksha-Android/1.0.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

print('=== STEP 1: HEALTH CHECK (api.getHealth) ===')
req = urllib.request.Request(f'{base_url}/api/v1/health', headers=headers)
with urllib.request.urlopen(req, timeout=60) as res:
    data = json.loads(res.read().decode())
    print(f'HTTP Status Code: {res.status}')
    print(f'Status Field: "{data.get("status")}"')
    print(f'Application: "{data.get("application")}"')
    print(f'Database Connected: {data.get("database_connected")}')
    healthy = data.get("status", "").lower() in ["healthy", "ok", "running"]
    print(f'isBackendHealthy() evaluation: {healthy}')

print('\n=== STEP 2: DEVICE REGISTRATION (api.registerDevice) ===')
test_device_id = str(uuid.uuid4())
reg_body = json.dumps({
    'device_id': test_device_id,
    'device_name': 'vivo V2065 (vivo Y31 Pro 5G)',
    'app_version': '1.0.0'
}).encode('utf-8')
req = urllib.request.Request(f'{base_url}/api/v1/devices/register', data=reg_body, headers=headers, method='POST')
with urllib.request.urlopen(req, timeout=60) as res:
    reg_data = json.loads(res.read().decode())
    print(f'HTTP Status Code: {res.status}')
    print(f'Registered Device ID: {reg_data.get("device_id")}')
    print(f'Registered Device Name: {reg_data.get("device_name")}')
    device_token = reg_data.get('device_token')
    print(f'Device Token: {device_token[:20]}...')

print('\n=== STEP 3: DEVICE STATUS (api.getDeviceStatus) ===')
auth_headers = dict(headers)
if device_token:
    auth_headers['X-Device-Token'] = device_token
req = urllib.request.Request(f'{base_url}/api/v1/devices/{test_device_id}/status', headers=auth_headers)
with urllib.request.urlopen(req, timeout=60) as res:
    status_data = json.loads(res.read().decode())
    print(f'HTTP Status Code: {res.status}')
    print(f'Security Posture: {status_data.get("security_posture")}')
    print(f'Protection Modules: {status_data.get("protection_modules")}')

print('\n=== STEP 4: SMS FRAUD ANALYSIS (api.analyzeMessage) ===')
sms_body = json.dumps({
    'device_id': test_device_id,
    'message_text': 'Dear SBI user, your KYC is expired. Click http://sbi-kyc-verify.xyz to update now.'
}).encode('utf-8')
req = urllib.request.Request(f'{base_url}/api/v1/mobile/analyze-message', data=sms_body, headers=auth_headers, method='POST')
with urllib.request.urlopen(req, timeout=60) as res:
    sms_res = json.loads(res.read().decode())
    print(f'HTTP Status Code: {res.status}')
    print(f'Risk Level: {sms_res.get("risk_level")}')
    print(f'Fraud Category: {sms_res.get("fraud_category")}')
    print(f'Risk Score: {sms_res.get("risk_score")}')

print('\n=== ALL ANDROID ENDPOINTS VERIFIED SUCCESSFULLY ===')
