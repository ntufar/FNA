# Financial Narrative Analyzer API Documentation

Complete REST API documentation for the Financial Narrative Analyzer platform.

## Table of Contents

- [Authentication](#authentication)
- [Company Management](#company-management)
- [Report Management](#report-management)
- [Analysis & Comparison](#analysis--comparison)
- [Alerts](#alerts)
- [Webhooks](#webhooks)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Code Examples](#code-examples)

## Base URL

- **Production**: `https://api.fna-platform.com/v1`
- **Staging**: `https://staging-api.fna-platform.com/v1`
- **Local Development**: `http://localhost:8000/v1`

## Authentication

The API supports two authentication methods:

### JWT Bearer Token (Recommended)

Most endpoints require a JWT bearer token obtained through the login endpoint.

**Header Format:**
```
Authorization: Bearer <access_token>
```

### API Key (Enterprise)

Enterprise tier users can use API keys for programmatic access.

**Header Format:**
```
X-API-Key: <api_key>
```

### Getting Started

1. **Register a new account:**
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "subscription_tier": "Basic"
}
```

2. **Login to get access token:**
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

3. **Use token in subsequent requests:**
```bash
GET /companies
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Company Management

### List Companies

Retrieve a list of companies with optional filtering.

**Endpoint:** `GET /companies`

**Query Parameters:**
- `ticker` (optional): Filter by ticker symbol
- `sector` (optional): Filter by industry sector
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 50, max: 200)

**Example Request:**
```bash
GET /companies?ticker=AAPL&limit=10
Authorization: Bearer <token>
```

**Example Response:**
```json
{
  "companies": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "ticker_symbol": "AAPL",
      "company_name": "Apple Inc.",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

### Add Company

Add a new company for tracking.

**Endpoint:** `POST /companies`

**Request Body:**
```json
{
  "ticker_symbol": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "industry": "Consumer Electronics"
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "ticker_symbol": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Get Company Details

**Endpoint:** `GET /companies/{company_id}`

**Example:**
```bash
GET /companies/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <token>
```

### Get Company Trends

Retrieve sentiment trend analysis for a company over time.

**Endpoint:** `GET /companies/{company_id}/trends`

**Query Parameters:**
- `periods` (optional): Number of reporting periods to include (default: 8)

**Example Response:**
```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "trend_data": [
    {
      "period": "Q1 2024",
      "optimism_score": 0.70,
      "risk_score": 0.35,
      "uncertainty_score": 0.25,
      "overall_sentiment": 0.65
    },
    {
      "period": "Q2 2024",
      "optimism_score": 0.75,
      "risk_score": 0.28,
      "uncertainty_score": 0.22,
      "overall_sentiment": 0.72
    }
  ],
  "trend_summary": {
    "overall_direction": "improving",
    "volatility": "moderate",
    "key_changes": [
      "Steady improvement in optimism scores",
      "Decreasing risk perception over time"
    ]
  }
}
```

---

## Report Management

### Upload Report

Upload a financial report file for analysis.

**Endpoint:** `POST /reports/upload`

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `file` (required): The report file (PDF, HTML, TXT, or iXBRL)
- `company_id` (required): UUID of the company
- `report_type` (required): Type of report (10-K, 10-Q, 8-K, Annual, Other)
- `fiscal_period` (optional): Fiscal period (e.g., "Q1 2024", "FY 2024")
- `filing_date` (optional): Filing date (ISO 8601 format)

**Example Request (cURL):**
```bash
curl -X POST "https://api.fna-platform.com/v1/reports/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@report.pdf" \
  -F "company_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "report_type=10-K" \
  -F "fiscal_period=FY 2024"
```

**Response:** `202 Accepted`
```json
{
  "report_id": "660e8400-e29b-41d4-a716-446655440001",
  "message": "Report uploaded successfully. Processing started.",
  "processing_status": "PROCESSING",
  "file_path": "uploads/550e8400/20240115_123456_report.pdf",
  "estimated_processing_time": "3-7 minutes"
}
```

### Download from SEC.gov

Automatically download a report from SEC.gov. Requires Pro or Enterprise subscription.

**Endpoint:** `POST /reports/download`

**Request Body:**
```json
{
  "ticker_symbol": "AAPL",
  "report_type": "10-K",
  "fiscal_year": 2024,
  "accession_number": "0000320193-24-000001",
  "filing_date": "2024-11-01"
}
```

**Note:** Either `accession_number` or `filing_date` can be provided to download a specific filing. If omitted, the latest filing of the specified type will be downloaded.

**Response:** `202 Accepted`
```json
{
  "report_id": "660e8400-e29b-41d4-a716-446655440001",
  "message": "SEC.gov report downloaded successfully for AAPL (10-K)",
  "processing_status": "PENDING",
  "file_path": "uploads/550e8400/20240115_123456_10-K.html",
  "estimated_processing_time": "3-7 minutes for SEC reports"
}
```

### Get Available SEC Filings

List available SEC filings for a company with download status.

**Endpoint:** `GET /reports/available-filings`

**Query Parameters:**
- `ticker_symbol` (required): Company ticker symbol (1-5 uppercase characters)
- `report_type` (required): Report type (10-K, 10-Q, 8-K)
- `fiscal_year` (optional): Filter by fiscal year

**Example Request:**
```bash
GET /reports/available-filings?ticker_symbol=AAPL&report_type=10-K&fiscal_year=2024
Authorization: Bearer <token>
```

**Example Response:**
```json
[
  {
    "accession_number": "0000320193-24-000001",
    "filing_date": "2024-11-01",
    "fiscal_period": "FY 2024",
    "report_type": "10-K",
    "is_downloaded": false,
    "existing_report_id": null,
    "file_format": "HTML",
    "report_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000001/aapl-20240928.htm"
  },
  {
    "accession_number": "0000320193-23-000001",
    "filing_date": "2023-11-03",
    "fiscal_period": "FY 2023",
    "report_type": "10-K",
    "is_downloaded": true,
    "existing_report_id": "660e8400-e29b-41d4-a716-446655440002",
    "file_format": "HTML",
    "report_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000001/aapl-20230930.htm"
  }
]
```

### Get Report Details

**Endpoint:** `GET /reports/{report_id}`

**Example Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "company_name": "Apple Inc.",
  "ticker_symbol": "AAPL",
  "report_type": "10-K",
  "fiscal_period": "FY 2024",
  "filing_date": "2024-11-01",
  "file_format": "HTML",
  "file_size_bytes": 5242880,
  "download_source": "SEC_AUTO",
  "processing_status": "COMPLETED",
  "created_at": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T10:35:00Z"
}
```

### Batch Process Reports

Process multiple reports in batch. Requires Pro or Enterprise subscription.

**Endpoint:** `POST /reports/batch`

**Request Body:**
```json
{
  "report_ids": [
    "660e8400-e29b-41d4-a716-446655440001",
    "660e8400-e29b-41d4-a716-446655440002",
    "660e8400-e29b-41d4-a716-446655440003"
  ]
}
```

**Limits:**
- Maximum 10 reports per batch
- Basic tier: 3 reports per batch
- Pro tier: 5 reports per batch
- Enterprise tier: 10 reports per batch

**Response:** `202 Accepted`
```json
{
  "batch_id": "770e8400-e29b-41d4-a716-446655440003",
  "status": "PROCESSING",
  "total_reports": 3,
  "successful": 0,
  "failed": 0,
  "results": [],
  "processed_at": "2024-01-15T10:40:00Z"
}
```

**Note:** With async job queue (T076), batch processing runs asynchronously. Use the batch status endpoint to check progress.

### Get Batch Status

**Endpoint:** `GET /reports/batch/{batch_id}`

**Example Response:**
```json
{
  "batch_id": "770e8400-e29b-41d4-a716-446655440003",
  "status": "PROCESSING",
  "total_reports": 3,
  "status_counts": {
    "PROCESSING": 2,
    "COMPLETED": 1,
    "FAILED": 0
  },
  "results": [
    {
      "report_id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "COMPLETED",
      "processed_at": "2024-01-15T10:42:00Z",
      "analysis_id": "880e8400-e29b-41d4-a716-446655440004"
    },
    {
      "report_id": "660e8400-e29b-41d4-a716-446655440002",
      "status": "PROCESSING",
      "processed_at": null,
      "analysis_id": null
    }
  ]
}
```

### Reanalyze Report

Trigger re-analysis of an existing report.

**Endpoint:** `POST /reports/{report_id}/analyze`

**Response:** `202 Accepted`
```json
{
  "message": "Re-analysis started for report 660e8400-e29b-41d4-a716-446655440001",
  "processing_status": "PROCESSING"
}
```

---

## Analysis & Comparison

### Get Report Analysis

Retrieve narrative analysis results for a report.

**Endpoint:** `GET /reports/{report_id}/analysis`

**Example Response:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440004",
  "report_id": "660e8400-e29b-41d4-a716-446655440001",
  "optimism_score": 0.72,
  "optimism_confidence": 0.89,
  "risk_score": 0.31,
  "risk_confidence": 0.85,
  "uncertainty_score": 0.28,
  "uncertainty_confidence": 0.82,
  "key_themes": [
    "Innovation and product development",
    "Market expansion",
    "Supply chain resilience",
    "Sustainability initiatives"
  ],
  "risk_indicators": [
    {
      "text": "may face challenges",
      "type": "modal_verb",
      "confidence": 0.75
    }
  ],
  "narrative_sections": {
    "mda": {
      "text": "Management's Discussion and Analysis...",
      "word_count": 5420
    },
    "ceo_letter": {
      "text": "Letter to Shareholders...",
      "word_count": 1230
    }
  },
  "financial_metrics": {
    "revenue": "$394.3 billion",
    "net_income": "$99.8 billion",
    "growth_rate": "2.8%"
  },
  "processing_time_seconds": 245,
  "model_version": "qwen3-4b-2507",
  "created_at": "2024-01-15T10:35:00Z"
}
```

### List Analyses

List all analyses with optional filtering.

**Endpoint:** `GET /analysis`

**Query Parameters:**
- `report_id` (optional): Filter by report ID
- `company_id` (optional): Filter by company ID
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records (default: 50, max: 500)

**Example Request:**
```bash
GET /analysis?company_id=550e8400-e29b-41d4-a716-446655440000&limit=10
Authorization: Bearer <token>
```

### Get Analysis Details

**Endpoint:** `GET /analysis/{analysis_id}`

### Compare Reports

Compare narrative tone between two financial reports.

**Endpoint:** `POST /analysis/compare`

**Request Body:**
```json
{
  "base_report_id": "660e8400-e29b-41d4-a716-446655440001",
  "comparison_report_id": "660e8400-e29b-41d4-a716-446655440002"
}
```

**Example Response:**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440005",
  "base_analysis_id": "880e8400-e29b-41d4-a716-446655440004",
  "comparison_analysis_id": "880e8400-e29b-41d4-a716-446655440006",
  "optimism_delta": 0.08,
  "risk_delta": -0.05,
  "uncertainty_delta": 0.02,
  "overall_sentiment_delta": 0.06,
  "significant_changes": [
    "Optimism increased by 8% (MODERATE)",
    "Risk decreased by 5% (MINOR)",
    "New theme: Market expansion strategy"
  ],
  "delta_summary": "improving"
}
```

### Similarity Search

Find similar narrative content using vector similarity search. Requires Enterprise subscription.

**Endpoint:** `POST /analysis/search/similar`

**Request Body:**
```json
{
  "query_text": "supply chain disruptions and manufacturing challenges",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "limit": 10
}
```

**Example Response:**
```json
{
  "results": [
    {
      "report_id": "660e8400-e29b-41d4-a716-446655440001",
      "analysis_id": "880e8400-e29b-41d4-a716-446655440004",
      "text_chunk": "We continue to face supply chain disruptions that may impact our manufacturing capabilities and delivery timelines...",
      "section_type": "RISK_FACTORS",
      "similarity_score": 0.9234,
      "company": "Apple Inc.",
      "ticker_symbol": "AAPL",
      "report_type": "10-K",
      "filing_date": "2024-11-01"
    },
    {
      "report_id": "660e8400-e29b-41d4-a716-446655440002",
      "analysis_id": "880e8400-e29b-41d4-a716-446655440005",
      "text_chunk": "Manufacturing challenges and supply constraints have affected our production capacity...",
      "section_type": "MD_A",
      "similarity_score": 0.8765,
      "company": "Apple Inc.",
      "ticker_symbol": "AAPL",
      "report_type": "10-Q",
      "filing_date": "2024-08-02"
    }
  ]
}
```

---

## Alerts

### List Alerts

Get list of alerts for the current user.

**Endpoint:** `GET /alerts`

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records (default: 50, max: 200)

**Example Response:**
```json
[
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440007",
    "alert_type": "SENTIMENT_SHIFT",
    "message": "Optimism increased by 12% for AAPL (Q1 2024 vs Q2 2024)",
    "severity": "MODERATE",
    "is_read": false
  },
  {
    "id": "bb0e8400-e29b-41d4-a716-446655440008",
    "alert_type": "RISK_INCREASE",
    "message": "Risk score increased by 8% for MSFT (FY 2023 vs FY 2024)",
    "severity": "MINOR",
    "is_read": true
  }
]
```

### Create Alert Preference

Configure alert preferences for a company.

**Endpoint:** `POST /alerts/preferences`

**Request Body:**
```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "alert_type": "SENTIMENT_SHIFT",
  "threshold_percentage": 10.0
}
```

**Threshold Range:** 5.0% - 50.0%

**Response:** `201 Created`
```json
{
  "user_id": "110e8400-e29b-41d4-a716-446655440009",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "alert_type": "SENTIMENT_SHIFT",
  "threshold_percentage": 10.0,
  "status": "accepted"
}
```

---

## Export Endpoints

### Export Analyses to CSV

Export analysis results to CSV format.

**Endpoint:** `GET /analysis/export/csv`

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `report_id` (optional): Filter by report ID

**Example Request:**
```bash
GET /analysis/export/csv?company_id=550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <token>
```

**Response:** CSV file download

### Export Analyses to Excel

Export analysis results to Excel format.

**Endpoint:** `GET /analysis/export/excel`

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `report_id` (optional): Filter by report ID

**Example Request:**
```bash
GET /analysis/export/excel?company_id=550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <token>
```

**Response:** Excel file (.xlsx) download

**Note:** Requires `openpyxl` package to be installed.

---

## Admin Endpoints

Admin endpoints require admin privileges. Contact support to request admin access.

### List Users

**Endpoint:** `GET /admin/users`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Records per page (default: 20, max: 100)
- `subscription_tier` (optional): Filter by subscription tier
- `is_active` (optional): Filter by active status

**Example Response:**
```json
{
  "users": [
    {
      "id": "110e8400-e29b-41d4-a716-446655440009",
      "email": "user@example.com",
      "subscription_tier": "Pro",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "last_login": "2024-01-20T14:30:00Z",
      "full_name": "John Doe"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

### Get User Details

**Endpoint:** `GET /admin/users/{user_id}`

### Update User

**Endpoint:** `PATCH /admin/users/{user_id}`

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "subscription_tier": "Enterprise",
  "is_active": true,
  "full_name": "John Doe Updated"
}
```

### Delete User (Soft Delete)

**Endpoint:** `DELETE /admin/users/{user_id}`

Soft deletes a user by setting `is_active=false`.

### Get Subscription Statistics

**Endpoint:** `GET /admin/stats/subscriptions`

**Example Response:**
```json
{
  "total_users": 150,
  "basic_tier": 80,
  "pro_tier": 50,
  "enterprise_tier": 20,
  "inactive_users": 5
}
```

### List Companies (Admin)

**Endpoint:** `GET /admin/companies`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Records per page (default: 20, max: 100)

---

## Health & Monitoring

### Health Check

**Endpoint:** `GET /health`

Comprehensive health check including database and cache status.

**Example Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "fna-platform",
  "timestamp": "2024-01-15T10:30:00Z",
  "database": {
    "status": "healthy",
    "connection": "ok"
  },
  "cache": {
    "sentiment_cache": {
      "size": 245,
      "maxsize": 1000,
      "type": "TTLCache"
    },
    "embedding_cache": {
      "size": 1523,
      "maxsize": 10000,
      "type": "LRUCache"
    },
    "analysis_cache": {
      "size": 89,
      "maxsize": 500,
      "type": "TTLCache"
    }
  },
  "checks": {
    "database": "ok",
    "cache": "ok"
  }
}
```

### Readiness Check

**Endpoint:** `GET /health/ready`

Kubernetes readiness probe endpoint.

### Liveness Check

**Endpoint:** `GET /health/live`

Kubernetes liveness probe endpoint.

### Metrics (Prometheus)

**Endpoint:** `GET /metrics`

Returns Prometheus-compatible metrics in text format.

**Example Response:**
```
# HELP fna_api_requests_total Total number of API requests
# TYPE fna_api_requests_total counter
fna_api_requests_total{endpoint="/companies",method="GET",status="200"} 1234
fna_api_requests_total{endpoint="/reports/upload",method="POST",status="202"} 567
...
```

### Metrics Summary

**Endpoint:** `GET /metrics/summary`

Human-readable metrics summary.

---

## Webhooks

Enterprise tier users can configure webhooks to receive notifications for significant narrative changes.

### Webhook Endpoints

**Endpoint:** `POST /webhooks/{webhook_id}/trigger`

Webhooks are triggered automatically when:
- Batch processing completes
- Significant narrative changes are detected
- Alert thresholds are exceeded

**Webhook Payload Example:**
```json
{
  "event_type": "BATCH_COMPLETED",
  "batch_id": "770e8400-e29b-41d4-a716-446655440003",
  "status": "COMPLETED",
  "total_reports": 3,
  "successful": 3,
  "failed": 0,
  "timestamp": "2024-01-15T10:45:00Z"
}
```

---

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `202 Accepted`: Request accepted for processing
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required or invalid credentials
- `403 Forbidden`: Insufficient permissions (subscription tier)
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Request valid but processing failed
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Common Error Codes:**
- `INVALID_CREDENTIALS`: Invalid email or password
- `INVALID_TOKEN`: Expired or invalid JWT token
- `SUBSCRIPTION_REQUIRED`: Feature requires higher subscription tier
- `BATCH_LIMIT_EXCEEDED`: Batch size exceeds subscription limit
- `RATE_LIMIT_EXCEEDED`: Too many requests, please retry later
- `REPORT_NOT_FOUND`: Report ID does not exist
- `ANALYSIS_NOT_READY`: Analysis still processing

---

## Rate Limiting

Rate limits are enforced per subscription tier:

| Tier | Requests per minute | Batch size limit |
|------|---------------------|------------------|
| Basic | 60 | 3 reports |
| Pro | 120 | 5 reports |
| Enterprise | 300 | 10 reports |

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

When rate limit is exceeded, a `429 Too Many Requests` response is returned with a `Retry-After` header indicating when to retry.

---

## Code Examples

### Python Example

```python
import requests

BASE_URL = "https://api.fna-platform.com/v1"

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "user@example.com",
        "password": "securepassword123"
    }
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Upload report
with open("report.pdf", "rb") as f:
    files = {"file": f}
    data = {
        "company_id": "550e8400-e29b-41d4-a716-446655440000",
        "report_type": "10-K",
        "fiscal_period": "FY 2024"
    }
    response = requests.post(
        f"{BASE_URL}/reports/upload",
        headers=headers,
        files=files,
        data=data
    )
    report_id = response.json()["report_id"]

# Get analysis (poll until ready)
import time
while True:
    response = requests.get(
        f"{BASE_URL}/reports/{report_id}/analysis",
        headers=headers
    )
    if response.status_code == 200:
        analysis = response.json()
        print(f"Optimism: {analysis['optimism_score']}")
        break
    elif response.status_code == 202:
        print("Still processing...")
        time.sleep(10)
    else:
        raise Exception(f"Error: {response.status_code}")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const BASE_URL = 'https://api.fna-platform.com/v1';

// Login
async function login(email, password) {
  const response = await axios.post(`${BASE_URL}/auth/login`, {
    email,
    password
  });
  return response.data.access_token;
}

// Upload and analyze report
async function analyzeReport(token, filePath, companyId) {
  const headers = { Authorization: `Bearer ${token}` };
  
  // Upload
  const FormData = require('form-data');
  const fs = require('fs');
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));
  form.append('company_id', companyId);
  form.append('report_type', '10-K');
  form.append('fiscal_period', 'FY 2024');
  
  const uploadResponse = await axios.post(
    `${BASE_URL}/reports/upload`,
    form,
    { headers: { ...headers, ...form.getHeaders() } }
  );
  
  const reportId = uploadResponse.data.report_id;
  
  // Poll for analysis
  while (true) {
    try {
      const analysisResponse = await axios.get(
        `${BASE_URL}/reports/${reportId}/analysis`,
        { headers }
      );
      return analysisResponse.data;
    } catch (error) {
      if (error.response?.status === 202) {
        console.log('Still processing...');
        await new Promise(resolve => setTimeout(resolve, 10000));
      } else {
        throw error;
      }
    }
  }
}

// Usage
(async () => {
  const token = await login('user@example.com', 'securepassword123');
  const analysis = await analyzeReport(
    token,
    './report.pdf',
    '550e8400-e29b-41d4-a716-446655440000'
  );
  console.log('Analysis:', analysis);
})();
```

### cURL Examples

```bash
# Login
curl -X POST "https://api.fna-platform.com/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"securepassword123"}'

# Upload report
curl -X POST "https://api.fna-platform.com/v1/reports/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@report.pdf" \
  -F "company_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "report_type=10-K" \
  -F "fiscal_period=FY 2024"

# Get analysis
curl -X GET "https://api.fna-platform.com/v1/reports/{report_id}/analysis" \
  -H "Authorization: Bearer <token>"

# Compare reports
curl -X POST "https://api.fna-platform.com/v1/analysis/compare" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "base_report_id": "660e8400-e29b-41d4-a716-446655440001",
    "comparison_report_id": "660e8400-e29b-41d4-a716-446655440002"
  }'
```

---

## Additional Resources

- [OpenAPI Specification](../specs/001-fna-platform/contracts/api-v1.yaml)
- [Postman Collection](../../postman/FNA-API-Collection.json)
- [Quick Start Guide](../SETUP.md)
- [Model Information](../docs/LM_STUDIO_SETUP.md)

---

**Last Updated:** 2024-01-15  
**API Version:** 1.0.0

