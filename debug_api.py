import requests
import json

url = "http://127.0.0.1:1234/v1/chat/completions"
headers = {"Content-Type": "application/json"}
payload = {
    "model": "qwen/qwen3-vl-8b",
    "messages": [
        {
            "role": "user",
            "content": "Analyze this: The company is doing well."
        }
    ],
    "temperature": 0.1,
    "top_p": 0.9,
    "max_tokens": 10000,
    "stream": False
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=3600)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    response.raise_for_status()
except Exception as e:
    print(f"Error: {e}")
