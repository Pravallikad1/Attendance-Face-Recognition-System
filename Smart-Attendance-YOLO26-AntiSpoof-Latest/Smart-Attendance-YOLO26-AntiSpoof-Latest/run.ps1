# PowerShell launch script for Smart Attendance System
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Smart Attendance System Server (Port 8000)...   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (Test-Path ".\.venv\Scripts\python.exe") {
    & ".\.venv\Scripts\uvicorn.exe" main:app --host 0.0.0.0 --port 8000 --reload
} else {
    Write-Host "Virtual environment .venv not found. Starting with global python..." -ForegroundColor Yellow
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}
