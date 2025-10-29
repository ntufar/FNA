# Quickstart Guide: Financial Narrative Analyzer Platform

**Target**: Get the FNA platform running locally in under 15 minutes

## Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **PostgreSQL 14+** with pgvector extension
- **Git** for version control
- **4GB+ available RAM** (for LLM inference)

## Environment Setup

### 1. Clone and Setup Repository

```bash
git clone https://github.com/your-org/fna-platform.git
cd fna-platform

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### 2. LM Studio Setup

```bash
# Download and install LM Studio from https://lmstudio.ai/
# 1. Open LM Studio
# 2. Go to "Discover" tab and search for "qwen/qwen3-4b-2507"  
# 3. Download the model (recommend Q4_K_M quantization)
# 4. Go to "Chat" tab and load the qwen/qwen3-4b-2507 model
# 5. Go to "Local Server" tab and start server on http://127.0.0.1:1234
# 6. Keep LM Studio running during FNA development/usage

# Test LM Studio connection
cd backend
python scripts/test_lm_studio.py
```

### 3. Database Setup

```bash
# Create PostgreSQL database (using localhost with postgres user)
createdb -h localhost -U postgres fna_development
# Password: qwerty123

# Enable pgvector extension
psql -h localhost -U postgres fna_development -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run database migrations (after environment setup below)
cd ../backend
alembic upgrade head
```

### 4. Environment Configuration

Create `backend/.env` file:

```bash
# Database (localhost PostgreSQL with credentials)
DATABASE_URL=postgresql://postgres:qwerty123@localhost:5432/fna_development

# LLM Configuration (qwen/qwen3-4b-2507 via LM Studio)
MODEL_NAME=qwen/qwen3-4b-2507
MODEL_API_URL=http://127.0.0.1:1234
MODEL_API_TIMEOUT=30
MODEL_MAX_TOKENS=512
MODEL_TEMPERATURE=0.1
MODEL_TOP_P=0.9

# SEC.gov API
SEC_USER_AGENT="YourCompany contact@yourcompany.com"
SEC_REQUEST_RATE_LIMIT=10

# Security
SECRET_KEY=your-secret-key-here
JWT_EXPIRE_HOURS=24

# Development
DEBUG=true
LOG_LEVEL=INFO
```

Create `frontend/.env` file:

```bash
VITE_API_BASE_URL=http://localhost:8000/v1
VITE_APP_TITLE="FNA Platform - Development"
```

## Quick Start

### 5. Start Backend Services

```bash
cd backend

# Test LM Studio connection (ensure LM Studio is running with qwen/qwen3-4b-2507 loaded)
python scripts/test_lm_studio.py

# Start FastAPI development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### 6. Start Frontend Development Server

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:5173

### 7. Verify Installation

Open http://localhost:5173 and you should see the FNA platform login page.

**Test API directly:**

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "version": "1.0.0", "model_ready": true}
```

## Basic Usage Examples

### 1. Upload and Analyze a Report

```bash
# Register a test user
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'

# Login to get access token
TOKEN=$(curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }' | jq -r .access_token)

# Add a company for tracking
COMPANY_ID=$(curl -X POST http://localhost:8000/v1/companies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker_symbol": "AAPL",
    "company_name": "Apple Inc."
  }' | jq -r .id)

# Upload a financial report (example with test file)
curl -X POST http://localhost:8000/v1/reports/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_data/sample_10k.pdf" \
  -F "company_id=$COMPANY_ID" \
  -F "report_type=10-K"
```

### 2. Auto-Download from SEC.gov

```bash
# Download latest 10-K for Apple
curl -X POST http://localhost:8000/v1/reports/download \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker_symbol": "AAPL",
    "report_type": "10-K"
  }'
```

### 3. View Analysis Results

```bash
# Get company reports
REPORTS=$(curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/companies/$COMPANY_ID/reports")

# Get analysis for a specific report
REPORT_ID="<report-id-from-above>"
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/reports/$REPORT_ID/analysis"
```

## Development Workflow

### Backend Development

```bash
cd backend

# Run tests
pytest tests/ -v

# Run with hot reload
uvicorn src.main:app --reload

# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Frontend Development

```bash
cd frontend

# Development server with hot reload
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix
```

### Full Stack Testing

```bash
# Start all services
docker-compose up -d  # If using Docker

# Run integration tests
cd backend
pytest tests/integration/ -v

# Run end-to-end tests
cd frontend
npm run test:e2e
```

## Key Configuration Files

### Backend Configuration

- `backend/src/config.py` - Application settings
- `backend/alembic.ini` - Database migration settings
- `backend/requirements.txt` - Python dependencies
- `backend/.env` - Environment variables (create from template)

### Frontend Configuration

- `frontend/vite.config.ts` - Build tool configuration
- `frontend/package.json` - Node dependencies and scripts
- `frontend/tsconfig.json` - TypeScript configuration
- `frontend/.env` - Environment variables (create from template)

## Performance Optimization

### Model Loading Optimization

```python
# In backend/src/services/sentiment_analyzer.py
# Adjust based on available RAM:

# For 8GB+ RAM systems:
MODEL_CONFIG = {
    "load_in_4bit": True,
    "device_map": "auto",
    "torch_dtype": "float16"
}

# For 4GB RAM systems:
MODEL_CONFIG = {
    "load_in_4bit": True,
    "device_map": "cpu",
    "torch_dtype": "float16"
}
```

### Database Query Optimization

```sql
-- Create performance indexes (run once)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_company_date 
ON financial_reports(company_id, filing_date DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analyses_report 
ON narrative_analyses(report_id);

-- pgvector index for similarity search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_vector 
ON narrative_embeddings USING ivfflat (embedding_vector vector_cosine_ops);
```

## Troubleshooting

### Common Issues

**Model Loading Errors:**
```bash
# Clear model cache and re-download
rm -rf backend/model_cache/
python -c "from src.services.sentiment_analyzer import SentimentAnalyzer; SentimentAnalyzer()"
```

**Database Connection Issues:**
```bash
# Check PostgreSQL is running
pg_isready

# Verify pgvector extension
psql fna_development -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

**Frontend Build Issues:**
```bash
# Clear Node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Memory Issues with LLM:**
- Reduce model quantization to 8-bit or use CPU-only mode
- Increase system swap space for development
- Consider using smaller model variants during development

### Debug Mode

Enable verbose logging by setting in `backend/.env`:
```bash
LOG_LEVEL=DEBUG
MODEL_VERBOSE=true
```

### Health Checks

```bash
# Verify all services are healthy
curl http://localhost:8000/health
curl http://localhost:5173/  # Should load frontend

# Check database connectivity
python -c "
from backend.src.database.connection import get_db_session
with get_db_session() as session:
    result = session.execute('SELECT version()')
    print('Database OK:', result.fetchone()[0])
"
```

## Next Steps

1. **Read the API Documentation**: Visit http://localhost:8000/docs for interactive API documentation
2. **Explore Sample Data**: Use the test datasets in `test_data/` directory
3. **Review Architecture**: See `data-model.md` for detailed database schema
4. **Performance Testing**: Run `backend/tests/performance/` for load testing
5. **Production Deployment**: Follow guides in `docs/deployment/`

## Support

- **Technical Issues**: Create issue in project repository
- **Development Questions**: See `docs/development/` for detailed guides
- **API Reference**: Interactive docs at `/docs` endpoint when backend is running

**Estimated Setup Time**: 10-15 minutes on modern hardware with stable internet connection.

