from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uvicorn
import sys
import os

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# API 密钥从环境变量读取（见 backend/.env.example），禁止硬编码

from api.charts import router as charts_router
from api.analysis import router as analysis_router
from api.ai_report import router as ai_report_router
from api.prompt_admin import router as prompt_admin_router
from api.redemption_codes import router as redemption_codes_router
from api.payments import router as payments_router
from api.manage_admin import router as manage_admin_router
from core.timezone_utils import get_timezone_from_coordinates

# 创建 FastAPI 应用
app = FastAPI(
    title="生命洞察命盘分析系统",
    description="基于八字、紫微斗数、印度星盘的综合命理分析系统",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class BirthInfoRequest(BaseModel):
    birth_date: str = Field(..., description="出生日期，格式：YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间，格式：HH:MM")
    longitude: float = Field(..., description="经度")
    latitude: float = Field(..., description="纬度")
    gender: int = Field(..., description="性别，1=男，0=女")
    location_name: Optional[str] = Field("", description="地点名称")
    daylight_saving: Optional[bool] = Field(False, description="是否使用夏令时")

class AnalysisRequest(BaseModel):
    chart_data: Dict[str, Any] = Field(..., description="三盘数据")
    analysis_type: str = Field(..., description="分析类型：personality, career, relationship, health")

# 挂载 API 路由
app.include_router(charts_router, prefix="/api/charts", tags=["命盘计算"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["命理分析"])
app.include_router(ai_report_router, prefix="/api/ai-report", tags=["AI报告生成"])
app.include_router(prompt_admin_router, prefix="/api/prompt-admin", tags=["Prompt管理"])
app.include_router(redemption_codes_router, tags=["兑换码管理"])
app.include_router(payments_router, tags=["在线支付"])
app.include_router(manage_admin_router)

# 根路径
@app.get("/")
async def root():
    return {
        "message": "生命洞察命盘分析系统 API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "lifeinsight-backend"}

# 时区查询端点
@app.get("/api/timezone")
async def get_timezone(longitude: float, latitude: float):
    """根据经纬度获取时区信息"""
    try:
        timezone_info = get_timezone_from_coordinates(longitude, latitude)
        return {
            "timezone": timezone_info["timezone"],
            "utc_offset": timezone_info["utc_offset"],
            "estimated": timezone_info.get("estimated", False),
            "location": f"经度{longitude}, 纬度{latitude}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"时区查询失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    ) 