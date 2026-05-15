"""
FastAPI 主入口 - 量化监控看板后端

启动方式:
    python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

Swagger 文档:
    http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import etf, fund, stock
from backend.utils.response import success

app = FastAPI(title="量化监控看板 API", version="1.0.0")

# CORS 中间件 - 允许本地前端端口跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite 默认端口
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(etf.router, prefix="/api/etf", tags=["ETF估值"])
app.include_router(fund.router, prefix="/api/fund", tags=["基金历史净值"])
app.include_router(stock.router, prefix="/api/stock", tags=["个股资金流向"])


@app.get("/api/ping", tags=["测试"])
async def ping():
    """健康检查接口"""
    return success(data={"status": "pong"}, msg="服务运行正常")
