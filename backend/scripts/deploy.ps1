# Deployment script for FNA Platform backend (PowerShell)
# Usage: .\scripts\deploy.ps1 [environment]
# Environment: development, staging, production

param(
    [string]$Environment = "production",
    [switch]$SkipTests = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "FNA Platform Backend Deployment" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Set-Location $ProjectRoot

# Load environment-specific configuration
$envFile = ".env.$Environment"
if (Test-Path $envFile) {
    Write-Host "Loading environment configuration from $envFile" -ForegroundColor Yellow
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# Check prerequisites
Write-Host ""
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is required but not installed" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
    Write-Host "WARNING: PostgreSQL client not found. Database migrations may fail." -ForegroundColor Yellow
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "$ProjectRoot\venv\Scripts\Activate.ps1"

# Install/upgrade dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
Write-Host ""
Write-Host "Running database migrations..." -ForegroundColor Yellow
alembic upgrade head

# Run database setup (vector indexes, etc.)
Write-Host ""
Write-Host "Setting up database indexes..." -ForegroundColor Yellow
python -c "
from src.database import init_database, setup_vector_environment
init_database()
setup_vector_environment()
print('Database setup completed')
"

# Run tests (optional)
if (-not $SkipTests) {
    Write-Host ""
    Write-Host "Running tests..." -ForegroundColor Yellow
    pytest tests/ -v --tb=short
    if ($LASTEXITCODE -ne 0) {
        $response = Read-Host "WARNING: Some tests failed. Continue deployment? (y/n)"
        if ($response -ne "y") {
            exit 1
        }
    }
}

# Create upload directories
Write-Host ""
Write-Host "Creating upload directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "uploads\reports" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "model_cache" | Out-Null

# Display deployment summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Environment: $Environment"
Write-Host "Python version: $(python --version)"
Write-Host "Database: $env:DATABASE_URL"
Write-Host "Log level: $env:LOG_LEVEL"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start the application:"
Write-Host "   uvicorn src.main:app --host 0.0.0.0 --port 8000"
Write-Host ""
Write-Host "2. Check health endpoint:"
Write-Host "   curl http://localhost:8000/health"
Write-Host ""
Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

