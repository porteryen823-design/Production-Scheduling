import requests
response = requests.post("http://localhost:8000/api/v1/simulation-planning-jobs/save", json={"key_value": "FINAL_CHECK", "remark": "Final check"})
print(response.json())
