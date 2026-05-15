"""
基金历史净值服务

数据源: AkShare fund_etf_fund_info_em
功能: 获取 ETF/基金的历史单位净值、累计净值、日增长率
"""
import time
import akshare as ak
import pandas as pd

# 缓存
_cache: dict = {}
CACHE_TTL = 300  # 5 分钟

# period 映射: 传入 period 字符串 → 回溯天数
PERIOD_DAYS = {
    "1m": 30,
    "3m": 90,
    "6m": 180,
    "1y": 365,
    "2y": 730,
    "3y": 1095,
}


def _validate_fund_code(code: str) -> bool:
    """校验基金/ETF 代码格式（6 位数字）"""
    return bool(code) and code.isdigit() and len(code) == 6


def _get_cache_key(code: str, period: str) -> str:
    return f"{code}_{period}"


def _get_cached(key: str) -> list | None:
    if key in _cache:
        entry = _cache[key]
        if time.time() - entry["time"] < CACHE_TTL:
            return entry["data"]
    return None


def _set_cache(key: str, data: list):
    _cache[key] = {"data": data, "time": time.time()}


def fetch_fund_history(fund_code: str, period: str = "1y") -> dict:
    """
    获取基金/ETF 历史净值

    Args:
        fund_code: 基金代码，如 "512010"
        period: 时间范围，可选 "1m"/"3m"/"6m"/"1y"/"2y"/"3y"

    Returns:
        {
            "fund_code": "512010",
            "period": "1y",
            "records": [{"date": "...", "nav": ..., "acc_nav": ..., "growth": ...}, ...],
            "summary": {"latest_date": ..., "latest_nav": ..., "period_high": ..., "period_low": ...}
        }
    """
    # 1. 校验参数
    if not _validate_fund_code(fund_code):
        raise ValueError(f"基金代码格式错误: '{fund_code}'，应为 6 位数字")

    if period not in PERIOD_DAYS:
        raise ValueError(f"period 参数错误: '{period}'，可选 {list(PERIOD_DAYS.keys())}")

    # 2. 检查缓存
    cache_key = _get_cache_key(fund_code, period)
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    # 3. 计算日期范围
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=PERIOD_DAYS[period])).strftime("%Y%m%d")

    # 4. 调用 AkShare，带重试
    max_retries = 3
    last_error = None
    df = None

    for attempt in range(max_retries):
        try:
            df = ak.fund_etf_fund_info_em(
                fund=fund_code,
                start_date=start_date,
                end_date=end_date,
            )
            break
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(1)
    else:
        raise ConnectionError(f"AkShare 请求失败（重试 {max_retries} 次）: {last_error}")

    # 5. 校验数据
    if df is None or df.empty:
        raise ValueError(f"基金代码 '{fund_code}' 在 {period} 内未查询到净值数据")

    # 6. 数据清洗 - 仅保留核心四列
    col_map = {}
    for col in df.columns:
        col_str = str(col).strip()
        if "净值日期" in col_str:
            col_map[col] = "date"
        elif "单位净值" in col_str:
            col_map[col] = "nav"
        elif "累计净值" in col_str:
            col_map[col] = "acc_nav"
        elif "日增长率" in col_str:
            col_map[col] = "growth"

    df = df.rename(columns=col_map)

    # 只保留需要的列
    keep_cols = [c for c in ["date", "nav", "acc_nav", "growth"] if c in df.columns]
    df = df[keep_cols]

    # 类型转换
    for col in ["nav", "acc_nav", "growth"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 7. 构造返回数据
    records = df.to_dict(orient="records")

    nav_series = df["nav"].dropna() if "nav" in df.columns else pd.Series()

    result = {
        "fund_code": fund_code,
        "period": period,
        "records": records,
        "summary": {
            "latest_date": records[-1]["date"] if records else "",
            "latest_nav": round(float(nav_series.iloc[-1]), 4) if len(nav_series) > 0 else 0,
            "period_high": round(float(nav_series.max()), 4) if len(nav_series) > 0 else 0,
            "period_low": round(float(nav_series.min()), 4) if len(nav_series) > 0 else 0,
            "total_records": len(records),
        },
    }

    # 8. 写入缓存
    _set_cache(cache_key, result)

    return result
