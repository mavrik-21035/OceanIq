# OceanIQ Backend Startup Script
# Run this from the project root: .\start_backend.ps1

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  OceanIQ Backend — Starting up..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- Check Ollama is running ---
Write-Host "[1/3] Checking Ollama..." -ForegroundColor Yellow
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    Write-Host "  ✅ Ollama is running (llama3 available)" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Ollama not detected — starting it now..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Write-Host "  ✅ Ollama started" -ForegroundColor Green
}

# --- Set working directory to project root (so oceaniq.db is found) ---
Set-Location $projectRoot

# --- Install minimal missing deps ---
Write-Host "[2/3] Verifying Python dependencies..." -ForegroundColor Yellow
pip install fastapi uvicorn[standard] sqlalchemy aiosqlite pydantic-settings httpx python-dotenv numpy --quiet --disable-pip-version-check
Write-Host "  ✅ Dependencies OK" -ForegroundColor Green

# --- Launch FastAPI ---
Write-Host "[3/3] Starting FastAPI backend on http://localhost:8000 ..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  API Docs  →  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Frontend  →  http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Press Ctrl+C to stop the backend." -ForegroundColor DarkGray
Write-Host ""

# Run uvicorn from project root so relative DB path resolves correctly
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend
