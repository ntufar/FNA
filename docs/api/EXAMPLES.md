# API Usage Examples

Practical examples for common use cases with the Financial Narrative Analyzer API.

## Table of Contents

- [Complete Workflow](#complete-workflow)
- [Batch Processing](#batch-processing)
- [Report Comparison](#report-comparison)
- [Trend Analysis](#trend-analysis)
- [Webhook Integration](#webhook-integration)

---

## Complete Workflow

### End-to-End Analysis Flow

```python
import requests
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000/v1"

def complete_analysis_workflow(
    email: str,
    password: str,
    ticker: str,
    report_type: str = "10-K"
) -> Dict[str, Any]:
    """Complete workflow: Login → Download → Analyze → Get Results"""
    
    # Step 1: Authenticate
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    login_response.raise_for_status()
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Download from SEC
    download_response = requests.post(
        f"{BASE_URL}/reports/download",
        headers=headers,
        json={
            "ticker_symbol": ticker,
            "report_type": report_type
        }
    )
    download_response.raise_for_status()
    report_data = download_response.json()
    report_id = report_data["report_id"]
    
    print(f"Report {report_id} downloaded. Processing...")
    
    # Step 3: Poll for analysis completion
    max_wait = 600  # 10 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        analysis_response = requests.get(
            f"{BASE_URL}/reports/{report_id}/analysis",
            headers=headers
        )
        
        if analysis_response.status_code == 200:
            analysis = analysis_response.json()
            print(f"Analysis complete!")
            print(f"Optimism: {analysis['optimism_score']:.2f}")
            print(f"Risk: {analysis['risk_score']:.2f}")
            print(f"Uncertainty: {analysis['uncertainty_score']:.2f}")
            return analysis
        elif analysis_response.status_code == 202:
            print("Still processing...")
            time.sleep(10)
        else:
            analysis_response.raise_for_status()
    
    raise TimeoutError("Analysis did not complete within timeout period")

# Usage
if __name__ == "__main__":
    result = complete_analysis_workflow(
        email="user@example.com",
        password="securepassword123",
        ticker="AAPL",
        report_type="10-K"
    )
```

---

## Batch Processing

### Process Multiple Reports Asynchronously

```python
import requests
import time
from typing import List

def batch_process_reports(
    token: str,
    report_ids: List[str]
) -> Dict[str, Any]:
    """Process multiple reports in batch and monitor progress."""
    
    BASE_URL = "http://localhost:8000/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Submit batch job
    batch_response = requests.post(
        f"{BASE_URL}/reports/batch",
        headers=headers,
        json={"report_ids": report_ids}
    )
    batch_response.raise_for_status()
    batch_data = batch_response.json()
    batch_id = batch_data["batch_id"]
    
    print(f"Batch {batch_id} submitted with {len(report_ids)} reports")
    
    # Monitor progress
    max_wait = 1800  # 30 minutes for batch
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        status_response = requests.get(
            f"{BASE_URL}/reports/batch/{batch_id}",
            headers=headers
        )
        status_response.raise_for_status()
        status_data = status_response.json()
        
        current_status = status_data["status"]
        if current_status != last_status:
            print(f"Batch status: {current_status}")
            print(f"  Completed: {status_data.get('successful', 0)}")
            print(f"  Failed: {status_data.get('failed', 0)}")
            last_status = current_status
        
        if current_status in ["COMPLETED", "FAILED", "PARTIALLY_COMPLETED"]:
            return status_data
        
        time.sleep(15)  # Check every 15 seconds
    
    raise TimeoutError("Batch processing did not complete within timeout")

# Usage
token = "your_jwt_token_here"
report_ids = [
    "660e8400-e29b-41d4-a716-446655440001",
    "660e8400-e29b-41d4-a716-446655440002",
    "660e8400-e29b-41d4-a716-446655440003"
]

result = batch_process_reports(token, report_ids)
print(f"Batch completed: {result['status']}")
```

---

## Report Comparison

### Compare Two Reports for Narrative Changes

```python
import requests

def compare_reports(
    token: str,
    base_report_id: str,
    comparison_report_id: str
) -> Dict[str, Any]:
    """Compare two reports and identify narrative changes."""
    
    BASE_URL = "http://localhost:8000/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    comparison_response = requests.post(
        f"{BASE_URL}/analysis/compare",
        headers=headers,
        json={
            "base_report_id": base_report_id,
            "comparison_report_id": comparison_report_id
        }
    )
    comparison_response.raise_for_status()
    comparison = comparison_response.json()
    
    print("Report Comparison Results:")
    print(f"Optimism Delta: {comparison['optimism_delta']:+.2%}")
    print(f"Risk Delta: {comparison['risk_delta']:+.2%}")
    print(f"Uncertainty Delta: {comparison['uncertainty_delta']:+.2%}")
    print(f"\nOverall Change: {comparison['delta_summary']}")
    print(f"\nSignificant Changes:")
    for change in comparison['significant_changes']:
        print(f"  - {change}")
    
    return comparison

# Usage
token = "your_jwt_token_here"
comparison = compare_reports(
    token,
    base_report_id="660e8400-e29b-41d4-a716-446655440001",
    comparison_report_id="660e8400-e29b-41d4-a716-446655440002"
)
```

---

## Trend Analysis

### Analyze Sentiment Trends Over Time

```python
import requests
import matplotlib.pyplot as plt
from typing import List, Dict

def get_company_trends(
    token: str,
    company_id: str,
    periods: int = 8
) -> Dict[str, Any]:
    """Get sentiment trends for a company."""
    
    BASE_URL = "http://localhost:8000/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    trends_response = requests.get(
        f"{BASE_URL}/companies/{company_id}/trends",
        headers=headers,
        params={"periods": periods}
    )
    trends_response.raise_for_status()
    return trends_response.json()

def visualize_trends(trends_data: Dict[str, Any]):
    """Visualize sentiment trends as a chart."""
    
    trend_data = trends_data.get("trend_data", [])
    if not trend_data:
        print("No trend data available")
        return
    
    periods = [item["period"] for item in trend_data]
    optimism = [item["optimism_score"] for item in trend_data]
    risk = [item["risk_score"] for item in trend_data]
    
    plt.figure(figsize=(12, 6))
    plt.plot(periods, optimism, marker='o', label='Optimism', color='green')
    plt.plot(periods, risk, marker='s', label='Risk', color='red')
    plt.xlabel('Period')
    plt.ylabel('Score')
    plt.title('Sentiment Trends Over Time')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

# Usage
token = "your_jwt_token_here"
company_id = "550e8400-e29b-41d4-a716-446655440000"

trends = get_company_trends(token, company_id, periods=8)
print(f"Trend Direction: {trends['trend_summary']['overall_direction']}")
visualize_trends(trends)
```

---

## Webhook Integration

### Set Up Webhook Handler for Batch Completion

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/webhook/batch-complete', methods=['POST'])
def handle_batch_complete():
    """Handle webhook notification for batch completion."""
    
    payload = request.json
    event_type = payload.get("event_type")
    batch_id = payload.get("batch_id")
    
    if event_type == "BATCH_COMPLETED":
        status = payload.get("status")
        successful = payload.get("successful", 0)
        failed = payload.get("failed", 0)
        
        print(f"Batch {batch_id} completed: {status}")
        print(f"  Successful: {successful}, Failed: {failed}")
        
        # Send notification email, update database, etc.
        send_notification(payload)
    
    return jsonify({"status": "received"}), 200

def send_notification(payload: Dict[str, Any]):
    """Send notification about batch completion."""
    # Implement your notification logic here
    # Email, Slack, SMS, etc.
    pass

if __name__ == "__main__":
    app.run(port=5000)
```

### Configure Webhook in API

```python
import requests

def configure_webhook(token: str, webhook_url: str):
    """Configure webhook endpoint for batch notifications."""
    
    BASE_URL = "http://localhost:8000/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    webhook_response = requests.post(
        f"{BASE_URL}/webhooks",
        headers=headers,
        json={
            "url": webhook_url,
            "events": ["BATCH_COMPLETED", "ALERT_TRIGGERED"]
        }
    )
    webhook_response.raise_for_status()
    return webhook_response.json()

# Usage
token = "your_jwt_token_here"
webhook_url = "https://your-domain.com/webhook/batch-complete"
webhook_config = configure_webhook(token, webhook_url)
print(f"Webhook configured: {webhook_config['webhook_id']}")
```

---

## Error Handling Best Practices

```python
import requests
from requests.exceptions import RequestException, HTTPError

def safe_api_call(func):
    """Decorator for safe API calls with error handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as e:
            if e.response.status_code == 401:
                print("Authentication failed. Please check credentials.")
            elif e.response.status_code == 403:
                print("Insufficient permissions. Check subscription tier.")
            elif e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After", "60")
                print(f"Rate limit exceeded. Retry after {retry_after} seconds.")
            elif e.response.status_code == 404:
                print("Resource not found.")
            else:
                print(f"HTTP Error {e.response.status_code}: {e.response.text}")
            raise
        except RequestException as e:
            print(f"Request failed: {e}")
            raise
    return wrapper

@safe_api_call
def get_analysis_safe(token: str, report_id: str):
    """Safely get analysis with error handling."""
    BASE_URL = "http://localhost:8000/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/reports/{report_id}/analysis",
        headers=headers
    )
    response.raise_for_status()
    return response.json()

# Usage
try:
    analysis = get_analysis_safe(token, report_id)
except Exception as e:
    print(f"Failed to get analysis: {e}")
```

---

**See Also:**
- [API Reference](README.md)
- [OpenAPI Specification](../../specs/001-fna-platform/contracts/api-v1.yaml)
- [Postman Collection](../../postman/FNA-API-Collection.json)

