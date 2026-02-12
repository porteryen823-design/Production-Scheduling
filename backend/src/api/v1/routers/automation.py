import os
import json
import asyncio
import subprocess
import sys
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from starlette.requests import Request

router = APIRouter(
    prefix="/automation",
    tags=["automation"]
)

# 測試腳本目錄路徑
# 在 Docker 環境中，我們將專案根目錄下的檔案掛載在根目錄或特定位置
# 這裡我們配合 docker-compose.yml 的掛載路徑
TEST_SCRIPTS_DIR = "/test_scripts"
BASE_DIR = "/"  # 專案根目錄掛載點

@router.get("/scripts", response_model=List[Dict[str, Any]])
async def list_scripts():
    """列出所有測試腳本"""
    if not os.path.exists(TEST_SCRIPTS_DIR):
        raise HTTPException(status_code=404, detail="Test scripts directory not found")
    
    scripts = []
    for filename in os.listdir(TEST_SCRIPTS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(TEST_SCRIPTS_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    scripts.append({
                        "id": filename,
                        "name": config.get("name", filename),
                        "description": config.get("description", ""),
                        "filename": filename
                    })
            except Exception as e:
                print(f"Error loading script {filename}: {e}")
    
    scripts.sort(key=lambda x: x["name"])
    return scripts

@router.get("/run-test/{script_name}")
async def run_test(script_name: str, request: Request):
    """執行自動化測試並串流輸出 (SSE)"""
    config_path = os.path.join(TEST_SCRIPTS_DIR, script_name)
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="Script configuration not found")

    runner_script_path = os.path.join(BASE_DIR, "automated_test_runner.py")
    
    async def event_generator():
        # 建構執行命令
        command = [
            sys.executable,
            "-u",
            runner_script_path,
            "--config", config_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=BASE_DIR
        )

        try:
            while True:
                # 檢查客戶端是否斷開
                if await request.is_disconnected():
                    process.terminate()
                    yield f"data: {json.dumps({'type': 'status', 'content': 'Client disconnected, terminating process...'})}\n\n"
                    break

                line = await process.stdout.readline()
                if not line:
                    break
                
                output = line.decode('utf-8', errors='ignore').strip()
                yield f"data: {json.dumps({'type': 'log', 'content': output})}\n\n"
            
            return_code = await process.wait()
            yield f"data: {json.dumps({'type': 'finished', 'code': return_code})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            if process.returncode is None:
                process.terminate()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
