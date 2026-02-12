"""
測試 automated_test_runner.py 的輸出是否正常
"""
import subprocess
import sys
import os

# =====================================================
# Windows Unicode Output Encoding Fix
# =====================================================
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 取得測試配置路徑
test_config = os.path.join(os.path.dirname(__file__), 'test_scripts', 'test_config_04.json')

print("Verifying Automated Test Runner...")
print(f"Using config: {test_config}")
print("-" * 60)

# Execute test
result = subprocess.run(
    [sys.executable, 'automated_test_runner.py', '--config', test_config],
    cwd=os.path.dirname(__file__),
    capture_output=False,  # Display output directly
    text=True
)

print("-" * 60)
if result.returncode == 0:
    print("✅ Test execution successful")
else:
    print(f"❌ Test execution failed (Code: {result.returncode})")
