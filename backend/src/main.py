"""
FastAPI 主應用程式
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from core.config import settings
from api.v1.routers import (
    lots,
    lot_operations,
    machines,
    operations,
    machine_unavailable_periods,
    dynamic_scheduling_job,
    ui_settings,
    simulation_data,
    dynamic_scheduling_job_snap,
    schedule
)

# 建立 FastAPI 應用程式
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
    生產排程系統 Web API
    
    提供完整的 CRUD 操作和資料查詢功能:
    - 工單管理 (Lots)
    - 工單作業管理 (LotOperations)
    - 機台與機台群組管理 (Machines, MachineGroups)
    - 作業狀態管理 (Completed, WIP, Frozen Operations)
    - 機台不可用時段管理 (MachineUnavailablePeriods)
    - 動態排程作業管理 (DynamicSchedulingJobs)
    - UI 介面參數管理 (UI Settings)
    - 模擬結果追蹤管理 (Simulation Data)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 設定 GZip 壓縮 (對於大型 JSON 如 machineTaskSegment 特別重要)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 註冊路由
app.include_router(lots.router, prefix=settings.API_PREFIX)
app.include_router(lot_operations.router, prefix=settings.API_PREFIX)
app.include_router(machines.router, prefix=settings.API_PREFIX)
app.include_router(operations.router, prefix=settings.API_PREFIX)
app.include_router(machine_unavailable_periods.router, prefix=settings.API_PREFIX)
app.include_router(dynamic_scheduling_job.router, prefix=settings.API_PREFIX)
app.include_router(ui_settings.router, prefix=settings.API_PREFIX)
app.include_router(simulation_data.router, prefix=settings.API_PREFIX)
app.include_router(dynamic_scheduling_job_snap.router, prefix=settings.API_PREFIX)

# 專為甘特圖設計的排程 API (在 /api 路徑下,不是 /api/v1)
app.include_router(schedule.router, prefix="/api")


@app.get("/")
def root():
    """根路徑"""
    return {
        "message": "生產排程系統 API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """健康檢查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
