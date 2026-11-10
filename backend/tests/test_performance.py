"""
backend/tests/test_performance.py
Stage 9: Performance Benchmarking & Concurrency Stress Test Suite.
Measures real response times, throughput, and p95/p99 latencies for all analysis endpoints.
"""
import time
import platform
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
TEST_BYPASS = {"x-test-bypass-rate-limit": "true"}


def test_performance_url_analysis_sequential():
    """Measure latency of 10 sequential URL scans."""
    urls = [
        "https://www.google.com",
        "https://www.github.com",
        "https://paypa1-security-verification.xyz/login.php",
        "https://www.wikipedia.org",
        "https://bank-update-kyc-alert.top/verify",
        "https://www.python.org",
        "https://irs-tax-refund-portal.click/claim",
        "https://www.microsoft.com",
        "https://sbi-netbanking-unblock.cc/auth",
        "https://www.stackoverflow.com"
    ]

    latencies = []
    for u in urls:
        start = time.perf_counter()
        res = client.post("/api/v1/detection/url", json={"url": u}, headers=TEST_BYPASS)
        duration_ms = (time.perf_counter() - start) * 1000.0
        assert res.status_code == 200
        latencies.append(duration_ms)

    latencies.sort()
    avg_lat = sum(latencies) / len(latencies)
    p95_lat = latencies[int(len(latencies) * 0.95)]
    min_lat = latencies[0]
    max_lat = latencies[-1]

    print(f"\n[URL Analysis Performance] Samples: {len(urls)}, Avg: {avg_lat:.2f}ms, Min: {min_lat:.2f}ms, Max: {max_lat:.2f}ms, p95: {p95_lat:.2f}ms")
    # Verify reasonable response time (< 5000ms on dev hardware)
    assert p95_lat < 5000.0


def test_performance_communication_analysis():
    """Measure latency of SMS/communication fraud detection."""
    messages = [
        "Your bank account will be blocked today. Click here to verify KYC immediately.",
        "Hi Mom, I lost my phone, this is my new WhatsApp number. Can you send 5000 Rs?",
        "Good morning, your package has been delivered to your doorstep.",
        "CBI Arrest Warrant issued in your name. Connect immediately on Skype video call.",
        "Your electricity bill is unpaid. Power will be disconnected by 9:30 PM tonight."
    ]

    latencies = []
    for msg in messages:
        start = time.perf_counter()
        res = client.post("/api/v1/communication/analyze", json={"message": msg}, headers=TEST_BYPASS)
        duration_ms = (time.perf_counter() - start) * 1000.0
        assert res.status_code == 200
        latencies.append(duration_ms)

    avg_lat = sum(latencies) / len(latencies)
    print(f"\n[Communication Analysis Performance] Samples: {len(messages)}, Avg: {avg_lat:.2f}ms")
    assert avg_lat < 3000.0


def test_performance_concurrent_url_scans():
    """Stress test with 10 concurrent URL scans using ThreadPoolExecutor."""
    urls = [
        f"https://test-concurrency-target-{i}.example.com/login"
        for i in range(10)
    ]

    def scan_url(target_url: str):
        start = time.perf_counter()
        res = client.post("/api/v1/detection/url", json={"url": target_url}, headers=TEST_BYPASS)
        duration_ms = (time.perf_counter() - start) * 1000.0
        return res.status_code, duration_ms

    start_total = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(scan_url, u) for u in urls]
        for f in as_completed(futures):
            results.append(f.result())

    total_time_ms = (time.perf_counter() - start_total) * 1000.0
    latencies = sorted([r[1] for r in results])
    success_count = sum(1 for r in results if r[0] == 200)

    avg_lat = sum(latencies) / len(latencies)
    p95_lat = latencies[int(len(latencies) * 0.95)]

    print(f"\n[Concurrent Stress Test] Workers: 5, Total Requests: {len(urls)}, Success: {success_count}/{len(urls)}")
    print(f"Total Wall Clock Time: {total_time_ms:.2f}ms, Avg Latency: {avg_lat:.2f}ms, p95 Latency: {p95_lat:.2f}ms")
    print(f"Test Environment: Node={platform.node()}, OS={platform.system()} {platform.release()}, Python={platform.python_version()}")

    assert success_count == len(urls)
    assert p95_lat < 5000.0
