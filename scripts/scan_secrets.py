import os
import re
import sys
import io

# 強制 Windows 輸出編碼為 UTF-8 (遵循規則 8-1)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

class SecretScanner:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        # 定義檢查模式：常見的變數名稱後接等號與引號字串
        self.patterns = {
            'password': r'(?i)(password|passwd|pwd)\s*=\s*["\'](?!.*os\.getenv)(.+?)["\']',
            'api_key': r'(?i)(api_key|apikey|secret_key|secret)\s*=\s*["\'](?!.*os\.getenv)(.+?)["\']',
            'token': r'(?i)(token|access_token)\s*=\s*["\'](?!.*os\.getenv)(.+?)["\']'
        }
        self.ignore_dirs = {'.git', 'venv', '__pycache__', 'node_modules', '.agent', '.roo', '.vscode'}

    def scan(self):
        print(f"--- Start Scanning Secrets in: {self.root_dir} ---")
        found_any = False
        
        for root, dirs, files in os.walk(self.root_dir):
            # 排除不掃描的目錄
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.env', '.json', '.html')):
                    file_path = os.path.join(root, file)
                    results = self.scan_file(file_path)
                    if results:
                        found_any = True
                        for res in results:
                            print(f"[!] Found potential secret in {file_path} (Line {res['line']}):")
                            print(f"    Type: {res['type']}")
                            print(f"    Content: {res['content']}")
                            print("-" * 50)
                            
        if not found_any:
            print("[+] No hardcoded secrets found! Excellent work.")
        print("--- Scan Completed ---")

    def scan_file(self, file_path):
        findings = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    for secret_type, pattern in self.patterns.items():
                        matches = re.finditer(pattern, line)
                        for match in matches:
                            # 排除空值或明顯的佔位符
                            val = match.group(2).strip()
                            if val and val.lower() not in ('""', "''", 'none', 'null', 'false', 'true'):
                                findings.append({
                                    'type': secret_type,
                                    'line': line_num,
                                    'content': line.strip()
                                })
        except Exception as e:
            print(f"Could not read {file_path}: {e}")
        return findings

if __name__ == "__main__":
    # 預設掃描當前目錄，或接收參數
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    scanner = SecretScanner(os.path.abspath(target))
    scanner.scan()
