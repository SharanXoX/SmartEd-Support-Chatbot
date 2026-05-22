# Stop stale SmartEd API processes and start a fresh uvicorn on port 8000.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $root "backend"

Write-Host "Stopping listeners on port 8000..."
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  ForEach-Object {
    try {
      Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    } catch { }
  }

Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match "uvicorn app\.main:app" } |
  ForEach-Object {
    Write-Host "Stopping uvicorn PID $($_.ProcessId)"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }

Start-Sleep -Seconds 2
$still = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($still) {
  Write-Warning "Port 8000 is still in use (PID $($still.OwningProcess)). Close other terminals running 'npm run dev' or restart Windows, then run this script again."
  exit 1
}

Write-Host "Starting API on http://127.0.0.1:8000 ..."
Set-Location $backend
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
