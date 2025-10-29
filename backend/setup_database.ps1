# PowerShell script to set up FNA database
# Requires PostgreSQL to be installed and running

$env:PGPASSWORD = "qwerty123"

Write-Host "Setting up FNA database..." -ForegroundColor Green

try {
    # Find PostgreSQL installation
    $psqlPath = Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\psql.exe" | Select-Object -First 1 -ExpandProperty FullName
    if (-not $psqlPath) {
        throw "PostgreSQL psql.exe not found in standard installation directory"
    }
    
    Write-Host "Using PostgreSQL at: $psqlPath" -ForegroundColor Cyan
    
    # Run the SQL setup script
    & $psqlPath -h localhost -U postgres -f backend/setup_database.sql
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database setup completed successfully!" -ForegroundColor Green
        Write-Host "Database: fna_development" -ForegroundColor Cyan
        Write-Host "Extensions: pgvector enabled" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Database setup failed!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
} finally {
    $env:PGPASSWORD = $null  # Clear password from environment
}
