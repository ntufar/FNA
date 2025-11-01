Param(
    [string]$Args = ""
)

# Ensure we run from backend directory
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
Set-Location -Path ..

# Set PYTHONPATH for src imports
$env:PYTHONPATH = "."

# Run pytest with optional args
if ([string]::IsNullOrWhiteSpace($Args)) {
    python -m pytest -q
} else {
    python -m pytest $Args
}

exit $LASTEXITCODE

