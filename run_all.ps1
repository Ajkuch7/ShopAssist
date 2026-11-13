$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$frontend = Join-Path $root 'frontend'

if (-not (Test-Path $python)) {
    throw "Python virtual environment not found at $python"
}
if (-not (Test-Path (Join-Path $frontend 'package.json'))) {
    throw "Frontend package not found at $frontend"
}

Start-Process -FilePath $python `
    -ArgumentList '-m uvicorn app.main:app --reload --port 8000' `
    -WorkingDirectory $root

Start-Process -FilePath 'npm.cmd' `
    -ArgumentList 'run dev -- --host=127.0.0.1 --port=5173' `
    -WorkingDirectory $frontend

Write-Host 'ShopAssist API: http://localhost:8000'
Write-Host 'ShopAssist UI:  http://localhost:5173'
Write-Host 'Health check:   http://localhost:8000/health'
Write-Host 'Logs:           logs/shopassist.log'
