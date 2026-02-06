import requests
import sys

BASE_URL = "http://localhost:8000/api/v1/simulation-planning-jobs"

def test_api():
    print("Testing DynamicSchedulingJob_Snap API...")
    
    # 1. List jobs
    print("\n1. Listing current simulation planning jobs...")
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            jobs = response.json()
            print(f"Success: Found {len(jobs)} jobs.")
        else:
            print(f"Error listing jobs: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"Connection failed: {e}. Is the backend running?")
        return

    # 2. Save current job (Requires at least one DynamicSchedulingJob to exist)
    print("\n2. Attempting to save current job...")
    payload = {"key_value": "Verification_Test", "remark": "Automated verification test"}
    response = requests.post(f"{BASE_URL}/save", json=payload)
    if response.status_code == 201:
        new_job = response.json()
        print(f"Success: Saved job ID {new_job['id']} with key '{new_job['key_value']}'")
        job_id = new_job['id']
    else:
        print(f"Error saving job: {response.status_code} - {response.text}")
        print("Note: This might fail if there's no DynamicSchedulingJob in the DB yet.")
        return

    # 3. List again
    print("\n3. Listing jobs again...")
    response = requests.get(BASE_URL)
    jobs = response.json()
    print(f"Total jobs now: {len(jobs)}")

    # 4. Load (Restore) job
    print(f"\n4. Restoring job ID {job_id}...")
    response = requests.post(f"{BASE_URL}/load/{job_id}")
    if response.status_code == 200:
        print(f"Success: Restored job. Result: {response.json()['message']}")
    else:
        print(f"Error restoring job: {response.status_code} - {response.text}")

    # 5. Delete job
    print(f"\n5. Deleting job ID {job_id}...")
    response = requests.delete(f"{BASE_URL}/{job_id}")
    if response.status_code == 204:
        print("Success: Deleted job.")
    else:
        print(f"Error deleting job: {response.status_code} - {response.text}")

    print("\nAPI Verification completed.")

if __name__ == "__main__":
    test_api()
