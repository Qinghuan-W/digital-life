$ErrorActionPreference = 'Stop'

$backendRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $backendRoot '.venv\Scripts\python.exe'
$postgresBin = 'C:\Program Files\PostgreSQL\17\bin'

if (-not (Test-Path -LiteralPath $python)) {
    throw 'backend/.venv is missing. Create it and install dependencies first.'
}
if (-not (Test-Path -LiteralPath (Join-Path $backendRoot '.env'))) {
    throw 'backend/.env is missing. Copy .env.example and add local secrets first.'
}

$env:Path = "$postgresBin;$env:Path"
Set-Location $backendRoot
& $python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
