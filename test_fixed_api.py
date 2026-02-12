import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import json
import mysql.connector
import os
from dotenv import load_dotenv

# =====================================================
# Windows Unicode Output Encoding Fix
# =====================================================
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


load_dotenv()

db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

print("=" * 60)
print("測試修復後的儲存 API")
print("=" * 60)

# 1. 先檢查 DynamicSchedulingJob 的記錄
print("\n[步驟 1] 檢查 DynamicSchedulingJob 資料...")
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)
cursor.execute('SELECT ScheduleId FROM DynamicSchedulingJob ORDER BY ScheduleId')
dynamic_jobs = cursor.fetchall()
print(f"✓ 找到 {len(dynamic_jobs)} 筆 DynamicSchedulingJob 記錄:")
for i, job in enumerate(dynamic_jobs, 1):
    print(f"  {i}. {job['ScheduleId']}")

# 2. 呼叫 API 儲存
print("\n[步驟 2] 呼叫 API 儲存模擬規劃...")
payload = {
    "key_value": "FIXED_TEST_01",
    "remark": "測試修復後的 API"
}

try:
    response = requests.post(
        "http://localhost:8000/api/v1/simulation-planning-jobs/save",
        json=payload
    )
    
    print(f"✓ API 回應 Status Code: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print(f"✓ API 回應顯示儲存了 {len(result)} 筆記錄")
        print("詳細資料:")
        for i, item in enumerate(result):
            print(f"  {i+1}. ID: {item.get('id')}, ScheduleId: {item.get('ScheduleId')}")
    else:
        print(f"✗ API 錯誤: {response.text}")
        cursor.close()
        conn.close()
        exit(1)
        
except Exception as e:
    print(f"✗ 連線錯誤: {e}")
    cursor.close()
    conn.close()
    exit(1)

# 3. 檢查資料庫中的 DynamicSchedulingJob_Snap
print("\n[步驟 3] 檢查資料庫中的 DynamicSchedulingJob_Snap...")
cursor.execute("""
    SELECT id, key_value, ScheduleId 
    FROM DynamicSchedulingJob_Snap 
    WHERE key_value = 'FIXED_TEST_01'
    ORDER BY ScheduleId
""")
saved_jobs = cursor.fetchall()
print(f"✓ 資料庫中找到 {len(saved_jobs)} 筆 key_value='FIXED_TEST_01' 的記錄:")
for i, job in enumerate(saved_jobs, 1):
    print(f"  {i}. ID: {job['id']}, ScheduleId: {job['ScheduleId']}")

# 4. 驗證結果
print("\n[步驟 4] 驗證結果...")
success = True

if len(saved_jobs) != len(dynamic_jobs):
    print(f"✗ 失敗：儲存的記錄數 ({len(saved_jobs)}) 與 DynamicSchedulingJob 記錄數 ({len(dynamic_jobs)}) 不符")
    success = False
else:
    print(f"✓ 記錄數正確：{len(saved_jobs)} 筆")

# 檢查 ScheduleId 是否都不同
saved_schedule_ids = set(job['ScheduleId'] for job in saved_jobs)
if len(saved_schedule_ids) != len(saved_jobs):
    print(f"✗ 失敗：儲存的記錄中有重複的 ScheduleId")
    success = False
else:
    print(f"✓ 所有 ScheduleId 都不同")

# 檢查 ScheduleId 是否與 DynamicSchedulingJob 一致
dynamic_schedule_ids = set(job['ScheduleId'] for job in dynamic_jobs)
if saved_schedule_ids != dynamic_schedule_ids:
    print(f"✗ 失敗：儲存的 ScheduleId 與 DynamicSchedulingJob 不一致")
    print(f"  DynamicSchedulingJob: {sorted(dynamic_schedule_ids)}")
    print(f"  DynamicSchedulingJob_Snap: {sorted(saved_schedule_ids)}")
    success = False
else:
    print(f"✓ 所有 ScheduleId 與 DynamicSchedulingJob 一致")

cursor.close()
conn.close()

print("\n" + "=" * 60)
if success:
    print("🎉 測試通過！修復成功！")
else:
    print("❌ 測試失敗，請檢查問題")
print("=" * 60)
