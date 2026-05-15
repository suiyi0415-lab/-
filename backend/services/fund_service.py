"""
基金历史净值服务

数据源: AkShare fund_etf_fund_info_em
功能: 获取 ETF/基金的历史单位净值、累计净值、日增长率
"""
import time
import requests
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


# ============================================================
# 基金穿透 - 前十大重仓股实时监控
# ============================================================

# 腾讯批量行情接口
TENCENT_QUOTE_URL = "https://qt.gtimg.cn/q="
TENCENT_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "text/plain"}


def _stock_to_tencent(code: str) -> str:
    """
    A 股代码转腾讯格式: 6xxxxx → sh6xxxxx, 0/3xxxxx → sz0/3xxxxx
    """
    if code.startswith(("6", "5")):
        return f"sh{code}"
    return f"sz{code}"


def _batch_realtime_quotes(codes: list[str]) -> dict:
    """
    批量获取实时行情（腾讯接口）

    Returns:
        {"600276": {"name": "恒瑞医药", "price": 53.99, "pct_change": -0.61}, ...}
    """
    if not codes:
        return {}

    tencent_codes = ",".join(_stock_to_tencent(c) for c in codes)
    try:
        r = requests.get(
            f"{TENCENT_QUOTE_URL}{tencent_codes}",
            headers=TENCENT_HEADERS,
            timeout=10,
        )
        r.encoding = "gbk"
    except Exception:
        return {}

    result = {}
    for line in r.text.strip().split(";"):
        line = line.strip()
        if not line:
            continue
        fields = line.split("~")
        if len(fields) < 33:
            continue
        code = fields[2]
        try:
            result[code] = {
                "name": fields[1],
                "price": float(fields[3]) if fields[3] else 0,
                "pct_change": float(fields[32]) if fields[32] else 0,
            }
        except (ValueError, IndexError):
            continue
    return result


def _batch_fund_flow(codes: list[str]) -> dict:
    """
    批量获取个股主力净流入（AkShare，可能因网络失败）

    Returns:
        {"600276": {"main_net_inflow": -1234567}, ...}
    """
    from backend.services.stock_service import _get_market

    result = {}
    for code in codes:
        try:
            market = _get_market(code)
            df = ak.stock_individual_fund_flow(stock=code, market=market)
            if df is not None and not df.empty:
                # 找到"主力净流入-净额"列
                for col in df.columns:
                    if "主力净流入" in str(col) and "净额" in str(col):
                        val = pd.to_numeric(df[col].iloc[-1], errors="coerce")
                        result[code] = {"main_net_inflow": float(val) if pd.notna(val) else 0}
                        break
        except Exception:
            # 单只失败不影响整体
            pass
        time.sleep(0.3)  # 控制请求频率
    return result


def fetch_fund_holdings_radar(fund_code: str) -> dict:
    """
    基金穿透：获取前十大重仓股的实时涨跌幅与资金动向

    Args:
        fund_code: ETF/基金代码，如 "512010"

    Returns:
        {
            "fund_code": "512010",
            "quarter": "2025年1季度",
            "estimated_pct": -0.82,
            "holdings": [
                {
                    "rank": 1,
                    "stock_code": "600276",
                    "stock_name": "恒瑞医药",
                    "weight": 17.39,
                    "price": 53.99,
                    "pct_change": -0.61,
                    "main_net_inflow": -12345678
                }, ...
            ]
        }
    """
    if not _validate_fund_code(fund_code):
        raise ValueError(f"基金代码格式错误: '{fund_code}'，应为 6 位数字")

    # 缓存检查
    cache_key = f"holdings_{fund_code}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    # 1. 获取最新季度重仓股
    max_retries = 3
    last_error = None
    df = None

    for attempt in range(max_retries):
        try:
            # 用最近的年份尝试
            from datetime import datetime
            year = str(datetime.now().year)
            df = ak.fund_portfolio_hold_em(symbol=fund_code, date=year)
            if df is None or df.empty:
                # 尝试上一年
                df = ak.fund_portfolio_hold_em(symbol=fund_code, date=str(int(year) - 1))
            break
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(1)
    else:
        raise ConnectionError(f"获取重仓股失败（重试 {max_retries} 次）: {last_error}")

    if df is None or df.empty:
        raise ValueError(f"基金代码 '{fund_code}' 未查询到重仓股数据")

    # 2. 取最新季度的前 10 只
    quarter = df["季度"].iloc[0] if "季度" in df.columns else ""
    top10 = df.head(10).copy()

    # 提取股票代码和权重
    stock_codes = []
    weights = {}
    for _, row in top10.iterrows():
        code = str(row.get("股票代码", "")).zfill(6)
        stock_codes.append(code)
        weights[code] = float(row.get("占净值比例", 0))

    # 3. 批量获取实时行情
    quotes = _batch_realtime_quotes(stock_codes)

    # 4. 尝试获取资金流向（可能失败，不影响主流程）
    flows = _batch_fund_flow(stock_codes)

    # 5. 组合数据
    holdings = []
    for i, code in enumerate(stock_codes):
        quote = quotes.get(code, {})
        flow = flows.get(code, {})
        holdings.append({
            "rank": i + 1,
            "stock_code": code,
            "stock_name": quote.get("name", top10.iloc[i].get("股票名称", "")),
            "weight": weights.get(code, 0),
            "price": quote.get("price", 0),
            "pct_change": quote.get("pct_change", 0),
            "main_net_inflow": flow.get("main_net_inflow"),
        })

    # 6. 计算估算当日涨跌幅 = Σ(单只涨跌幅 × 权重) / Σ(权重)
    total_weight = sum(h["weight"] for h in holdings)
    if total_weight > 0:
        estimated_pct = sum(
            h["pct_change"] * h["weight"] for h in holdings
        ) / total_weight
    else:
        estimated_pct = 0.0

    result = {
        "fund_code": fund_code,
        "quarter": quarter,
        "estimated_pct": round(estimated_pct, 2),
        "holdings": holdings,
    }

    # 写入缓存
    _set_cache(cache_key, result)

    return result


# ============================================================
# 实时分时数据 - 供 ECharts 走势图使用
# ============================================================

TENCENT_MINUTE_URL = "https://web.ifzq.gtimg.cn/appstock/app/minute/query"


def _code_to_tencent(code: str) -> str:
    """ETF 代码转腾讯格式"""
    if code.startswith(("5", "6")):
        return f"sh{code}"
    return f"sz{code}"


def fetch_fund_intraday(code: str) -> dict:
    """
    获取今日分时数据（1 分钟级）

    Args:
        code: ETF/股票代码，如 "512010"

    Returns:
        {
            "code": "512010",
            "date": "2026-05-15",
            "pre_close": 0.360,
            "records": [
                {"time": "09:30", "price": 0.359, "avg_price": 0.359, "volume": 90743},
                {"time": "09:31", "price": 0.359, "avg_price": 0.359, "volume": 577300},
                ...
            ]
        }
    """
    if not _validate_fund_code(code):
        raise ValueError(f"代码格式错误: '{code}'，应为 6 位数字")

    # 缓存（分时数据 30 秒刷新一次）
    cache_key = f"intraday_{code}"
    if code in _cache:
        entry = _cache[code]
        if time.time() - entry["time"] < 30 and entry.get("key") == cache_key:
            return entry["data"]

    tencent_code = _code_to_tencent(code)

    try:
        r = requests.get(
            TENCENT_MINUTE_URL,
            params={"code": tencent_code},
            headers=TENCENT_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        raw = r.json()
    except Exception as e:
        raise ConnectionError(f"分时数据请求失败: {str(e)}")

    # 解析数据
    stock_data = raw.get("data", {}).get(tencent_code, {})
    minute_list = stock_data.get("data", {}).get("data", [])

    if not minute_list:
        raise ValueError(f"代码 '{code}' 今日暂无分时数据（可能未开盘）")

    # 昨收价
    pre_close = stock_data.get("data", {}).get("pre_close", 0)
    try:
        pre_close = float(pre_close)
    except (ValueError, TypeError):
        pre_close = 0

    # 清洗为列表（腾讯数据为累积量，需做差值得每分钟数据）
    records = []
    prev_vol = 0
    prev_amount = 0.0

    for item in minute_list:
        parts = str(item).split()
        if len(parts) < 3:
            continue

        # 时间: HHMM → HH:MM
        raw_time = parts[0]
        if len(raw_time) == 4:
            time_str = f"{raw_time[:2]}:{raw_time[2:]}"
        else:
            time_str = raw_time

        try:
            price = float(parts[1])
            cum_vol = int(parts[2])
            cum_amount = float(parts[3]) if len(parts) > 3 else 0
        except (ValueError, IndexError):
            continue

        # 差值：每分钟成交量和成交额
        minute_vol = max(cum_vol - prev_vol, 0)
        minute_amount = max(cum_amount - prev_amount, 0.0)
        prev_vol = cum_vol
        prev_amount = cum_amount

        # 均价 = 每分钟成交额 / 每分钟成交量（和 price 同单位）
        if minute_vol > 0 and minute_amount > 0:
            avg_price = round(minute_amount / minute_vol / 100, 4)
        else:
            avg_price = price

        records.append({
            "time": time_str,
            "price": price,
            "avg_price": avg_price,
            "volume": minute_vol,
        })

    # 获取日期（用最后一条数据的时间推断）
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    result = {
        "code": code,
        "date": today,
        "pre_close": pre_close,
        "records": records,
    }

    # 写入缓存（用特殊 key 标记）
    _cache[code] = {"data": result, "time": time.time(), "key": cache_key}

    return result
