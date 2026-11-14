import os
import sys
import time
import tracemalloc

sys.path.insert(0, r"C:\Users\RAHUL\OneDrive\Desktop\cyberRaksha")
sys.path.insert(0, r"C:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\backend")

tracemalloc.start()
t0 = time.perf_counter()

from app.main import app
from fastapi.testclient import TestClient

t_import = time.perf_counter() - t0

client = TestClient(app)
t_client = time.perf_counter() - t0

# 1. Health check
t_h0 = time.perf_counter()
r_h = client.get("/health")
t_health = (time.perf_counter() - t_h0) * 1000

# 2. Phishing URL Inference
t_u0 = time.perf_counter()
r_u = client.post("/api/v1/detection/url", json={"url": "http://sbi-netbanking-update.xyz/login"})
t_url = (time.perf_counter() - t_u0) * 1000

# 3. Second warm URL inference
t_u1 = time.perf_counter()
r_u2 = client.post("/api/v1/detection/url", json={"url": "http://hdfc-kyc-verify.xyz/login"})
t_url_warm = (time.perf_counter() - t_u1) * 1000

# 4. Digital Arrest Scam Inference
t_d0 = time.perf_counter()
r_d = client.post("/api/v1/communication/digital-arrest/analyze", json={"message": "URGENT: CBI officer speaking. You are under digital arrest. Pay fine to safe account immediately."})
t_digital_arrest = (time.perf_counter() - t_d0) * 1000

# 5. Second warm communication inference
t_d1 = time.perf_counter()
r_d2 = client.post("/api/v1/communication/digital-arrest/analyze", json={"message": "Police notice: warrant issued against Aadhaar. Transfer funds to avoid arrest."})
t_digital_arrest_warm = (time.perf_counter() - t_d1) * 1000

tracemalloc_peak_mb = tracemalloc.get_traced_memory()[1] / (1024 * 1024)
tracemalloc.stop()

print(f"Startup Time: {t_client:.2f}s (import: {t_import:.2f}s)")
print(f"Tracemalloc Peak Python RAM: {tracemalloc_peak_mb:.2f} MB")
print(f"Health check latency: {t_health:.2f} ms")
print(f"URL detection (cold): {t_url:.2f} ms | result={r_u.json().get('classification')}")
print(f"URL detection (warm): {t_url_warm:.2f} ms | result={r_u2.json().get('classification')}")
print(f"Digital arrest (cold): {t_digital_arrest:.2f} ms | result={r_d.json().get('classification')}")
print(f"Digital arrest (warm): {t_digital_arrest_warm:.2f} ms | result={r_d2.json().get('classification')}")
