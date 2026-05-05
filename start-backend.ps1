# Kill all Python processes immediately
Write-Host "Killing all Python processes..."
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

# Set env and start
$env:PYTHONPATH = "$PSScriptRoot\backend"
Push-Location "$PSScriptRoot\backend"

try {
    Write-Host "Starting LegalClear backend..."
    python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload --timeout-keep-alive 1800 --timeout-graceful-shutdown 1800
} finally {
    Pop-Location
}
