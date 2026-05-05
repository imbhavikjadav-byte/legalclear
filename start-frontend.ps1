# Kill any Node process on port 5173 (Vite default)
Write-Host "Killing any Node processes on port 5173..."
$lines = netstat -ano | Select-String ":5173"
foreach ($line in $lines) {
    $parts = $line.ToString().Trim() -split '\s+'
    $pidVal = $parts[-1]
    if ($pidVal -match '^\d+$' -and [int]$pidVal -gt 4) {
        try {
            Write-Host "Killing PID $pidVal"
            Stop-Process -Id ([int]$pidVal) -Force -ErrorAction Stop
        } catch {
            Write-Host "Could not kill PID $pidVal (may already be stopped)"
        }
    }
}
Start-Sleep -Seconds 1

Push-Location "$PSScriptRoot\frontend"

try {
    Write-Host "Starting LegalClear frontend..."
    npm run dev
} finally {
    Pop-Location
}
