"""
批次加工功能測試腳本
用於驗證 STEP5 的批次加工邏輯是否正確運作
"""

import json
import os
import sys
import io
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def analyze_batch_processing_results():
    """分析排程結果中的批次加工情況"""
    
    result_file = "plan_result/LotStepResult.json"
    
    if not os.path.exists(result_file):
        print("❌ 找不到排程結果檔案，請先執行排程")
        return
    
    with open(result_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # 篩選出 STEP5 的所有記錄
    step5_records = [r for r in results if r['Step'] == 'STEP5']
    
    if not step5_records:
        print("⚠️  沒有找到 STEP5 的排程記錄")
        return
    
    print(f"\n{'='*80}")
    print(f"批次加工分析報告 - STEP5")
    print(f"{'='*80}\n")
    print(f"總共有 {len(step5_records)} 個 Lots 在 STEP5 加工\n")
    
    # 按照開始時間分組（同一批次的 Lots 開始時間相同）
    batches = {}
    for record in step5_records:
        start_time = record['Start']
        if start_time not in batches:
            batches[start_time] = []
        batches[start_time].append(record)
    
    print(f"識別出 {len(batches)} 個批次\n")
    print(f"{'-'*80}\n")
    
    # 分析每個批次
    batch_num = 1
    for start_time, lots in sorted(batches.items()):
        print(f"📦 批次 {batch_num}:")
        print(f"   開始時間: {start_time}")
        print(f"   批次大小: {len(lots)} 個 Lots")
        print(f"   Lot IDs: {', '.join([lot['LotId'] for lot in lots])}")
        
        # 檢查結束時間是否一致
        end_times = set([lot['End'] for lot in lots])
        if len(end_times) == 1:
            print(f"   結束時間: {end_times.pop()} ✓ (所有 Lots 同時結束)")
        else:
            print(f"   ⚠️  警告：結束時間不一致！")
            for lot in lots:
                print(f"      - {lot['LotId']}: {lot['End']}")
        
        # 計算加工時間
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(lots[0]['End'])
        duration = (end_dt - start_dt).total_seconds() / 60
        print(f"   加工時間: {duration:.0f} 分鐘")
        
        # 檢查機台
        machines = set([lot['Machine'] for lot in lots])
        if len(machines) == 1:
            print(f"   使用機台: {machines.pop()} ✓ (同一台機器)")
        else:
            print(f"   使用機台: {', '.join(machines)} (多台機器)")
        
        print()
        batch_num += 1
    
    print(f"{'-'*80}\n")
    
    # 驗證批次大小限制
    max_batch_size = int(os.getenv('BATCH_PROCESSING_MAX_SIZE', 2))
    oversized_batches = [b for b in batches.values() if len(b) > max_batch_size]
    
    if oversized_batches:
        print(f"❌ 發現 {len(oversized_batches)} 個批次超過大小限制 (MAX={max_batch_size})")
    else:
        print(f"✓ 所有批次都符合大小限制 (MAX={max_batch_size})")
    
    # 計算平均批次大小
    avg_batch_size = sum(len(b) for b in batches.values()) / len(batches)
    print(f"✓ 平均批次大小: {avg_batch_size:.2f} 個 Lots")
    
    # 計算批次利用率
    utilization = (avg_batch_size / max_batch_size) * 100
    print(f"✓ 批次利用率: {utilization:.1f}%")
    
    print(f"\n{'='*80}\n")

def check_waiting_time():
    """檢查等待時間是否符合限制"""
    
    result_file = "plan_result/LotStepResult.json"
    
    if not os.path.exists(result_file):
        return
    
    with open(result_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    max_wait_time = int(os.getenv('BATCH_PROCESSING_MAX_WAIT_MINUTES', 10))
    
    print(f"等待時間分析 (上限: {max_wait_time} 分鐘)")
    print(f"{'-'*80}\n")
    
    # 為每個 Lot 找到 STEP4 和 STEP5 的時間
    lots_data = {}
    for record in results:
        lot_id = record['LotId']
        if lot_id not in lots_data:
            lots_data[lot_id] = {}
        lots_data[lot_id][record['Step']] = {
            'Start': record['Start'],
            'End': record['End']
        }
    
    # 計算等待時間（STEP4 結束到 STEP5 開始）
    violations = []
    for lot_id, steps in lots_data.items():
        if 'STEP4' in steps and 'STEP5' in steps:
            step4_end = datetime.fromisoformat(steps['STEP4']['End'])
            step5_start = datetime.fromisoformat(steps['STEP5']['Start'])
            wait_time = (step5_start - step4_end).total_seconds() / 60
            
            if wait_time > max_wait_time:
                violations.append((lot_id, wait_time))
            
            print(f"  {lot_id}: 等待 {wait_time:.1f} 分鐘", end="")
            if wait_time > max_wait_time:
                print(f" ❌ 超過限制")
            else:
                print(f" ✓")
    
    print()
    if violations:
        print(f"❌ 發現 {len(violations)} 個 Lots 等待時間超過限制")
    else:
        print(f"✓ 所有 Lots 的等待時間都在限制內")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n" + "="*80)
    print("批次加工功能驗證工具")
    print("="*80 + "\n")
    
    analyze_batch_processing_results()
    check_waiting_time()
    
    print("驗證完成！\n")
