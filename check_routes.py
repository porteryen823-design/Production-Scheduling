
import requests

try:
    response = requests.get("http://localhost:8000/openapi.json")
    if response.status_code == 200:
        data = response.json()
        paths = data.get("paths", {}).keys()
        print("Available paths:")
        for path in sorted(paths):
            print(path)
    else:
        print(f"Failed to get openapi.json: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
