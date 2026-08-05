$ErrorActionPreference = 'Stop'

$backendRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $backendRoot '.venv\Scripts\python.exe'
$postgresBin = 'C:\Program Files\PostgreSQL\17\bin'

if (-not (Test-Path -LiteralPath $python)) {
    throw 'backend/.venv is missing. Create it and install dependencies first.'
}

$env:Path = "$postgresBin;$env:Path"
$env:APP_ENV = 'test'
Set-Location $backendRoot
& $python -m pytest
exit $LASTEXITCODE
