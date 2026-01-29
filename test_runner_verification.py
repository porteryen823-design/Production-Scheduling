"""
測試 automated_test_runner.py 的輸出是否正常
"""
import subprocess
import sys
import os

# 取得測試配置路徑
test_config = os.path.join(os.path.dirname(__file__), 'test_scripts', 'test_config_04.json')

print("測試自動化測試執行器...")
print(f"使用配置: {test_config}")
print("-" * 60)

# 執行測試
result = subprocess.run(
    [sys.executable, 'automated_test_runner.py', '--config', test_config],
    cwd=os.path.dirname(__file__),
    capture_output=False,  # 直接顯示輸出
    text=True
)

print("-" * 60)
if result.returncode == 0:
    print("✅ 測試執行成功")
else:
    print(f"❌ 測試執行失敗 (代碼: {result.returncode})")
