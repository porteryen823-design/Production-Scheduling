import requests
import json

payload = {
    "key_value": "DEBUG_SERIAL",
    "remark": "Debug with db info"
}

response = requests.post("http://localhost:8000/api/v1/simulation-planning-jobs/save", json=payload)
print(f"Status: {response.status_code}")
try:
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error parsing JSON: {e}")
    print(f"Raw response: {response.text}")
