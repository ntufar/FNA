# FNA Platform - Postman API Collection

This directory contains comprehensive Postman collections and environments for testing the Financial Narrative Analyzer (FNA) platform API.

## 📁 Files Overview

### Collection
- **`FNA-API-Collection.json`** - Complete API collection with all endpoints, tests, and examples

### Environments
- **`environments/Development.postman_environment.json`** - Local development environment (localhost:8000)
- **`environments/Staging.postman_environment.json`** - Staging environment configuration
- **`environments/Production.postman_environment.json`** - Production environment configuration

## 🚀 Quick Setup

### 1. Import Collection and Environments

1. **Open Postman** and click **Import**
2. **Import Collection**: Select `FNA-API-Collection.json`
3. **Import Environments**: Select all three environment files from `environments/` folder

### 2. Select Environment

1. Click the **Environment dropdown** (top right)
2. Select **"FNA Development"** for local testing
3. Select **"FNA Staging"** or **"FNA Production"** for deployed environments

### 3. Authentication Flow

1. **Start with Authentication folder**
2. **Run "User Login"** request with valid credentials:
   ```json
   {
     "email": "demo@fna-platform.com",
     "password": "SecurePass123!"
   }
   ```
3. **Access token is automatically stored** in collection variables
4. **All subsequent requests** will use the stored token

## 📋 Collection Structure

### 🔐 Authentication
- **User Login** - Authenticate and get JWT token
- **User Register** - Create new user account  
- **Get User Profile** - Retrieve authenticated user info

### 🏢 Companies
- **List Companies** - Get all tracked companies with filtering
- **Add Company** - Add new company for tracking
- **Get Company Reports** - Retrieve all reports for a company

### 📊 Reports
- **Upload Report** - Upload financial report file for analysis
- **Download from SEC.gov** - Auto-download latest SEC filings
- **Batch Process Reports** - Process multiple reports simultaneously

### 🧠 Analysis
- **Get Report Analysis** - Retrieve sentiment analysis results
- **Compare Reports** - Generate delta analysis between two reports

### 📈 Dashboard
- **Get Company Trends** - Sentiment trends over time

### 🚨 Alerts
- **Get Alerts** - Retrieve user alerts
- **Mark Alert as Read** - Update alert status
- **Get/Set Alert Preferences** - Manage alert configuration

### 🔍 Search
- **Find Similar Narratives** - Vector-based semantic search

### ❤️ Health Checks
- **General Health Check** - Overall system status
- **Liveness Probe** - Kubernetes liveness endpoint
- **Readiness Probe** - Kubernetes readiness endpoint

## 🧪 Testing Features

### Automated Testing
Each request includes **comprehensive test scripts**:
- ✅ **Status code validation**
- ✅ **Response schema validation**
- ✅ **Business logic assertions**
- ✅ **Automatic variable extraction** (IDs, tokens)

### Test Execution
1. **Individual Request**: Click **Send** to run with tests
2. **Folder Testing**: Right-click folder → **Run folder**
3. **Full Collection**: Use **Runner** to execute entire collection

### Example Test Output
```javascript
✓ Login successful
✓ Response contains access token
✓ Access token stored successfully
```

## 🔧 Configuration

### Environment Variables
Each environment includes:
- **`host`** - API base URL
- **`environment`** - Deployment stage
- **`debug`** - Logging level

Development environment also includes:
- **`lm_studio_url`** - Local LM Studio server
- **`postgres_host`** - Local PostgreSQL host

### Collection Variables (Auto-managed)
- **`access_token`** - JWT authentication token
- **`company_id`** - Last created/retrieved company ID
- **`report_id`** - Last uploaded/downloaded report ID
- **`analysis_id`** - Last analysis result ID

## 🏃‍♂️ Usage Workflows

### 1. Complete Report Analysis Workflow
```
1. User Login → Get token
2. Add Company → Store company_id
3. Upload Report OR Download from SEC.gov → Store report_id
4. Get Report Analysis → Retrieve results
5. Compare Reports → Delta analysis
```

### 2. Batch Processing Workflow
```
1. User Login → Authentication
2. Batch Process Reports → Multiple companies
3. Monitor processing status
4. Retrieve analysis results
```

### 3. Alert Management Workflow
```
1. User Login → Authentication
2. Set Alert Preferences → Configure thresholds
3. Get Alerts → Monitor notifications
4. Mark Alert as Read → Update status
```

## 🛠️ Development Tips

### Custom Request Examples
Update request bodies with your own data:
- **Company Tickers**: Change "NVDA" to your target companies
- **File Uploads**: Update file paths in upload requests
- **Alert Thresholds**: Adjust percentage values
- **Search Queries**: Modify semantic search text

### Environment Switching
- **Development**: Local testing with debug logging
- **Staging**: Pre-production testing
- **Production**: Live API with minimal logging

### Token Management
- Tokens **auto-refresh** on login
- **Expiry tracking** prevents invalid requests
- **Global pre-request script** handles token validation

## 🐛 Troubleshooting

### Common Issues

**❌ "Unauthorized" errors**
- Run "User Login" request first
- Check token expiry in collection variables
- Verify credentials in environment

**❌ "Connection refused" errors**
- Ensure local server is running (`uvicorn src.main:app --reload`)
- Check host URL in selected environment
- Verify PostgreSQL and LM Studio are running

**❌ "File not found" in uploads**
- Update file path in upload request body
- Use absolute file paths
- Check file format (PDF, HTML, TXT, iXBRL)

### Debug Mode
Enable debug logging by:
1. Set environment variable `debug: true`
2. Check **Postman Console** (View → Show Postman Console)
3. Review request/response logs

## 🔄 Updates and Maintenance

### Adding New Endpoints
1. **Add request** to appropriate folder
2. **Include test scripts** for validation
3. **Update this README** with new workflow
4. **Export updated collection** after changes

### Environment Updates
- **Development**: Update when local setup changes
- **Staging/Production**: Update when deployed URLs change
- **Variables**: Add new variables as needed for new features

---

## 📞 Support

For API issues or questions:
- **Collection Issues**: Check test scripts and error messages
- **Environment Issues**: Verify host URLs and credentials
- **API Issues**: Check application logs and health endpoints

**Ready to analyze financial narratives with AI! 🚀**
