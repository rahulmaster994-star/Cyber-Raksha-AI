# Cyber Raksha AI - Easy Startup Script for Windows PowerShell
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "              CYBER RAKSHA AI ECOSYSTEM                   " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$RootPath = "c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha"
Set-Location $RootPath

# 1. Check Python Venv
$PythonExe = Join-Path $RootPath "backend\venv\Scripts\python.exe"
$UvicornExe = Join-Path $RootPath "backend\venv\Scripts\uvicorn.exe"

if (-Not (Test-Path $PythonExe)) {
    Write-Host "[!] Virtual environment not found at backend\venv. Please install dependencies first." -ForegroundColor Red
    exit 1
}

Write-Host "[+] Virtual environment found." -ForegroundColor Green

# 2. Set PYTHONPATH
$env:PYTHONPATH = "$RootPath;$RootPath\backend"
Write-Host "[+] Set PYTHONPATH to include backend and root." -ForegroundColor Green

# 3. Verify AI Model
$ModelFile = Join-Path $RootPath "ai_engine\models\phishing\phishing_classifier.joblib"
if (-Not (Test-Path $ModelFile)) {
    Write-Host "[*] AI Model not found. Training model now..." -ForegroundColor Yellow
    & $PythonExe "$RootPath\ai_engine\training\train_model.py"
} else {
    Write-Host "[+] AI Model verified." -ForegroundColor Green
}

# 4. Display Endpoints
Write-Host ""
Write-Host "Services will be accessible at:" -ForegroundColor Cyan
Write-Host "  - Backend API:       http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  - Swagger API Docs:  http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  - Health Endpoint:   http://127.0.0.1:8000/health" -ForegroundColor White
Write-Host "  - Dashboard (Dev):   http://localhost:5173 (run 'npm run dev' in frontend)" -ForegroundColor White
Write-Host "  - Browser Extension: Load unpacked from $RootPath\browser_extension" -ForegroundColor White
Write-Host ""
Write-Host "[*] Launching Uvicorn Server on 127.0.0.1:8000 (Ctrl+C to stop)..." -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

& $UvicornExe app.main:app --host 127.0.0.1 --port 8000 --reload

