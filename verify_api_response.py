import requests
import json

payload = {
    "key_value": "VERIFY_LOGIC",
    "remark": "Verifying the join logic"
}

try:
    response = requests.post("http://localhost:8000/api/v1/simulation-planning-jobs/save", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
