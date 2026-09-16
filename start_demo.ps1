<#
.SYNOPSIS
OPSINTEL POC Startup Script

.DESCRIPTION
This script automatically starts both the FastAPI backend and the Vite frontend
for the OPSINTEL demo.

.NOTES
Requires Python 3.10+ and Node.js to be installed.
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Starting OPSINTEL POC Demo Environment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Reset Database and Generate Data
Write-Host "`n[1/3] Generating synthetic deterministic data..." -ForegroundColor Yellow
$env:PYTHONPATH = (Get-Location).Path
& .\backend\.venv\Scripts\python.exe scripts\generate_data.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Data generation failed."
    exit 1
}

# 2. Start Backend
Write-Host "`n[2/3] Starting FastAPI Backend (Port 8000)..." -ForegroundColor Yellow
Start-Process -FilePath ".\backend\.venv\Scripts\uvicorn.exe" -ArgumentList "backend.main:app --host 0.0.0.0 --port 8000" -NoNewWindow

# Wait a second for backend to boot
Start-Sleep -Seconds 2

# 3. Start Frontend
Write-Host "`n[3/3] Starting React Frontend (Port 5173)..." -ForegroundColor Yellow
Set-Location .\frontend
Start-Process -FilePath "npm" -ArgumentList "run dev"

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host " OPSINTEL is now running!" -ForegroundColor Green
Write-Host " Backend API: http://localhost:8000/docs" -ForegroundColor Green
Write-Host " Dashboard:   http://localhost:5173" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "`nPress Ctrl+C in the terminal running 'npm run dev' to stop the frontend."
Write-Host "You may need to manually kill the uvicorn process depending on your terminal."
