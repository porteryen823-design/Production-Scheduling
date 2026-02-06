import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import json

# Test the save API
print("=== 測試儲存 API ===")
payload = {
    "key_value": "TEST_API_CALL",
    "remark": "測試 API 呼叫"
}

try:
    response = requests.post(
        "http://localhost:8000/api/v1/simulation-planning-jobs/save",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 201:
        result = response.json()
        print(f"\n成功儲存 {len(result)} 筆記錄:")
        for i, record in enumerate(result, 1):
            print(f"  {i}. ID: {record.get('id', 'N/A')}, ScheduleId: {record.get('ScheduleId', 'N/A')}, Key: {record.get('key_value', 'N/A')}")
    else:
        print(f"\nError: {response.text}")
        
except Exception as e:
    print(f"Exception: {e}")
