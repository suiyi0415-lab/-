"""
ETF 路由 - API 接口定义

GET /api/etf/history?code=512010
获取指定 ETF 的近一年历史净值及估值百分位
"""
from fastapi import APIRouter, Query
from backend.services.etf_service import fetch_etf_history
from backend.utils.response import success, error

router = APIRouter()


@router.get("/history")
async def get_etf_history(code: str = Query(..., description="ETF 代码，如 512010")):
    """
    获取 ETF 近一年历史净值

    Query 参数:
        code: ETF 代码（6 位数字，以 5 或 1 开头）

    返回示例:
        {
            "code": 200,
            "data": {
                "etf_code": "512010",
                "records": [{"date": "2025-05-15", "close": 0.412, ...}],
                "summary": {
                    "latest_date": "2026-05-15",
                    "latest_close": 0.359,
                    "year_high": 0.420,
                    "year_low": 0.320,
                    "percentile": 25.5
                }
            },
            "msg": "success"
        }
    """
    try:
        data = fetch_etf_history(code)
        return success(data=data)
    except ValueError as e:
        return error(msg=str(e), code=400)
    except ConnectionError as e:
        return error(msg=str(e), code=502)
    except Exception as e:
        return error(msg=f"服务器内部错误: {str(e)}", code=500)
