#!/bin/bash
# Deployment script for FNA Platform backend
# Usage: ./scripts/deploy.sh [environment]
# Environment: development, staging, production

set -e  # Exit on error

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "FNA Platform Backend Deployment"
echo "Environment: $ENVIRONMENT"
echo "=========================================="

cd "$PROJECT_ROOT"

# Load environment-specific configuration
if [ -f ".env.$ENVIRONMENT" ]; then
    echo "Loading environment configuration from .env.$ENVIRONMENT"
    export $(cat .env.$ENVIRONMENT | grep -v '^#' | xargs)
fi

# Check prerequisites
echo ""
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed"
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo "ERROR: PostgreSQL client is required but not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
echo ""
echo "Running database migrations..."
alembic upgrade head

# Run database setup (vector indexes, etc.)
echo ""
echo "Setting up database indexes..."
python -c "
from src.database import init_database, setup_vector_environment
init_database()
setup_vector_environment()
print('Database setup completed')
"

# Run tests (optional, can be skipped with --skip-tests)
if [[ "$*" != *"--skip-tests"* ]]; then
    echo ""
    echo "Running tests..."
    pytest tests/ -v --tb=short || {
        echo "WARNING: Some tests failed. Continue deployment? (y/n)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }
fi

# Collect static files (if any)
echo ""
echo "Preparing static files..."
# Add static file collection commands here if needed

# Create upload directories
echo ""
echo "Creating upload directories..."
mkdir -p uploads/reports
mkdir -p logs
mkdir -p model_cache

# Set permissions
chmod 755 uploads/reports
chmod 755 logs

# Display deployment summary
echo ""
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo "Environment: $ENVIRONMENT"
echo "Python version: $(python3 --version)"
echo "Database: $DATABASE_URL"
echo "Log level: ${LOG_LEVEL:-INFO}"
echo ""
echo "Next steps:"
echo "1. Start the application:"
echo "   uvicorn src.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "2. Or use systemd service (if configured):"
echo "   sudo systemctl start fna-backend"
echo ""
echo "3. Check health endpoint:"
echo "   curl http://localhost:8000/health"
echo ""
echo "Deployment completed successfully!"
echo "=========================================="

