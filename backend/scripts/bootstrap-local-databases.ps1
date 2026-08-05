$ErrorActionPreference = 'Stop'

$backendRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent $backendRoot
$psql = 'C:\Program Files\PostgreSQL\17\bin\psql.exe'
$markerDirectory = Join-Path $projectRoot '.artifacts'
$successMarker = Join-Path $markerDirectory 'postgres-bootstrap.ok'
$failureMarker = Join-Path $markerDirectory 'postgres-bootstrap.failed'

if (-not (Test-Path -LiteralPath $psql)) {
    throw 'PostgreSQL 17 psql.exe was not found.'
}

if (-not $env:DIGITALLIFE_DB_PASSWORD -or -not $env:DIGITALLIFE_JWT_SECRET) {
    throw 'Required bootstrap secrets are missing from the process environment.'
}

New-Item -ItemType Directory -Force -Path $markerDirectory | Out-Null
Remove-Item -LiteralPath $successMarker, $failureMarker -Force -ErrorAction SilentlyContinue

$temporarySql = Join-Path ([System.IO.Path]::GetTempPath()) "digitallife-postgres-$([guid]::NewGuid().ToString('N')).sql"
$sql = @"
DO `$bootstrap`$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'digitallife_user') THEN
        CREATE ROLE digitallife_user LOGIN;
    END IF;
END
`$bootstrap`$;

ALTER ROLE digitallife_user WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD '$($env:DIGITALLIFE_DB_PASSWORD)';

SELECT 'CREATE DATABASE digitallife OWNER digitallife_user'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'digitallife')\gexec

SELECT 'CREATE DATABASE digitallife_test OWNER digitallife_user'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'digitallife_test')\gexec

ALTER DATABASE digitallife OWNER TO digitallife_user;
ALTER DATABASE digitallife_test OWNER TO digitallife_user;
"@

try {
    [System.IO.File]::WriteAllText($temporarySql, $sql, [System.Text.UTF8Encoding]::new($false))

    Write-Host 'Enter the postgres administrator password when prompted.'
    & $psql --no-psqlrc --quiet -W -h localhost -p 5432 -U postgres -d postgres -v ON_ERROR_STOP=1 -f $temporarySql
    if ($LASTEXITCODE -ne 0) {
        throw 'PostgreSQL bootstrap failed. Check the password and server status.'
    }

    $databaseUrl = 'postgresql+psycopg://' + 'digitallife_user:' + $env:DIGITALLIFE_DB_PASSWORD + '@localhost:5432/digitallife'
    $testDatabaseUrl = 'postgresql+psycopg://' + 'digitallife_user:' + $env:DIGITALLIFE_DB_PASSWORD + '@localhost:5432/digitallife_test'
    $jwtLine = 'JWT' + '_SECRET=' + $env:DIGITALLIFE_JWT_SECRET
    $environmentFile = @"
APP_ENV=development
APP_NAME=DigitalLife API
API_V1_PREFIX=/api/v1
DATABASE_URL=$databaseUrl
TEST_DATABASE_URL=$testDatabaseUrl
$jwtLine
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
"@
    [System.IO.File]::WriteAllText((Join-Path $backendRoot '.env'), $environmentFile, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllText($successMarker, 'ok', [System.Text.UTF8Encoding]::new($false))
    Write-Host 'DigitalLife PostgreSQL databases were created successfully.' -ForegroundColor Green
} catch {
    [System.IO.File]::WriteAllText($failureMarker, $_.Exception.Message, [System.Text.UTF8Encoding]::new($false))
    Write-Error $_
    exit 1
} finally {
    Remove-Item -LiteralPath $temporarySql -Force -ErrorAction SilentlyContinue
    Remove-Item Env:DIGITALLIFE_DB_PASSWORD, Env:DIGITALLIFE_JWT_SECRET -ErrorAction SilentlyContinue
}
