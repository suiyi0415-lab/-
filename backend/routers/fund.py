"""
基金历史净值路由

GET /api/fund/history?fund_code=512010&period=1y
"""
from fastapi import APIRouter, Query
from backend.services.fund_service import fetch_fund_history
from backend.utils.response import success, error

router = APIRouter()


@router.get("/history")
async def get_fund_history(
    fund_code: str = Query(..., description="基金/ETF 代码，如 512010"),
    period: str = Query("1y", description="时间范围: 1m/3m/6m/1y/2y/3y"),
):
    """
    获取基金/ETF 历史净值

    - **fund_code**: 基金或 ETF 代码（6 位数字）
    - **period**: 时间范围，可选 1m(月) / 3m / 6m / 1y(年) / 2y / 3y

    返回: 日期、单位净值、累计净值、日增长率
    """
    try:
        data = fetch_fund_history(fund_code, period)
        return success(data=data)
    except ValueError as e:
        return error(msg=str(e), code=400)
    except ConnectionError as e:
        return error(msg=str(e), code=502)
    except Exception as e:
        return error(msg=f"服务器内部错误: {str(e)}", code=500)
