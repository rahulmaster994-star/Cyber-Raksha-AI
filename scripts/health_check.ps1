# Cyber Raksha AI - Comprehensive Health Check Script
Write-Host "Checking Cyber Raksha AI services..." -ForegroundColor Cyan

$RootPath = "c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha"
$PythonExe = Join-Path $RootPath "backend\venv\Scripts\python.exe"

# 1. Check Backend API Health
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[PASS] Backend API is running: Status = $($res.status)" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Backend API is not currently running on http://127.0.0.1:8000. Start it with .\start_cyberraksha.ps1" -ForegroundColor Yellow
}

# 2. Check AI Engine Model
$ModelFile = Join-Path $RootPath "ai_engine\models\phishing\phishing_classifier.joblib"
if (Test-Path $ModelFile) {
    $size = (Get-Item $ModelFile).Length / 1KB
    Write-Host "[PASS] AI Classifier Model exists: $($size.ToString('F2')) KB" -ForegroundColor Green
} else {
    Write-Host "[FAIL] AI Classifier Model missing at $ModelFile" -ForegroundColor Red
}

# 3. Check SQLite DB
$DbFile = Join-Path $RootPath "backend\cyberraksha.db"
if (Test-Path $DbFile) {
    Write-Host "[PASS] SQLite Database found." -ForegroundColor Green
} else {
    Write-Host "[INFO] SQLite Database will be created on first launch." -ForegroundColor Gray
}

# 4. Check Frontend build
$FrontendDist = Join-Path $RootPath "frontend\dist\index.html"
if (Test-Path $FrontendDist) {
    Write-Host "[PASS] Frontend production build exists in frontend\dist." -ForegroundColor Green
} else {
    Write-Host "[INFO] Frontend production build not generated yet. Run 'npm run build' in frontend/ to generate." -ForegroundColor Gray
}

Write-Host "Health check completed." -ForegroundColor Cyan

