"""
个股资金流向路由

GET /api/stock/market_flow?stock_code=300308
"""
from fastapi import APIRouter, Query
from backend.services.stock_service import fetch_stock_flow
from backend.utils.response import success, error

router = APIRouter()


@router.get("/market_flow")
async def get_market_flow(
    stock_code: str = Query(..., description="股票代码，如 300308"),
):
    """
    获取个股资金流向及高位风险指标

    - **stock_code**: A 股代码（6 位数字）

    返回: 主力/超大单/大单/中单/小单净流入、涨跌幅、年内高点对比
    """
    try:
        data = fetch_stock_flow(stock_code)
        return success(data=data)
    except ValueError as e:
        return error(msg=str(e), code=400)
    except ConnectionError as e:
        return error(msg=str(e), code=502)
    except Exception as e:
        return error(msg=f"服务器内部错误: {str(e)}", code=500)
