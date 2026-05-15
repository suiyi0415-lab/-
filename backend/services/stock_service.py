"""
个股资金流向服务

数据源: AkShare stock_individual_fund_flow
功能: 获取个股主力资金动向、计算高位风险指标
"""
import time
import akshare as ak
import pandas as pd
import requests

# 缓存
_cache: dict = {}
CACHE_TTL = 300  # 5 分钟

# 股票代码前缀 → 交易所 market 参数
MARKET_MAP = {
    "6": "sh",   # 上海主板 / 科创板
    "5": "sh",   # 上海 ETF
    "0": "sz",   # 深圳主板
    "3": "sz",   # 创业板
    "1": "sz",   # 深圳 ETF / 可转债
}

# 新浪实时行情接口（用于获取历史最高价参考）
SINA_QUOTE_URL = "https://qt.gtimg.cn/q="


def _validate_stock_code(code: str) -> bool:
    """校验股票代码格式（6 位数字）"""
    return bool(code) and code.isdigit() and len(code) == 6


def _get_market(code: str) -> str:
    """根据股票代码首位判断交易所"""
    prefix = code[0]
    if prefix in MARKET_MAP:
        return MARKET_MAP[prefix]
    return "sz"  # 默认深圳


def _get_sina_symbol(code: str) -> str:
    """转为新浪代码格式"""
    market = _get_market(code)
    return f"{market}{code}"


def _get_cached(key: str) -> dict | None:
    if key in _cache:
        entry = _cache[key]
        if time.time() - entry["time"] < CACHE_TTL:
            return entry["data"]
    return None


def _set_cache(key: str, data: dict):
    _cache[key] = {"data": data, "time": time.time()}


def fetch_stock_flow(stock_code: str) -> dict:
    """
    获取个股资金流向及高位风险指标

    Args:
        stock_code: 股票代码，如 "300308"

    Returns:
        {
            "stock_code": "300308",
            "stock_name": "中际旭创",
            "latest": {
                "date": "2026-05-15",
                "close": 1049.87,
                "pct_change": -2.61,
                "main_net_inflow": -1446789000,
                "main_net_ratio": -4.94,
                "super_big_net_inflow": -165027600,
                "big_net_inflow": -1281761000,
                ...
            },
            "flow_trend": [{"date": "...", "close": ..., "main_net_inflow": ...}, ...],
            "risk": {
                "year_high": ...,
                "current_vs_high_pct": ...,
                "near_high_warning": true/false
            }
        }
    """
    # 1. 校验
    if not _validate_stock_code(stock_code):
        raise ValueError(f"股票代码格式错误: '{stock_code}'，应为 6 位数字")

    # 2. 缓存
    cached = _get_cached(stock_code)
    if cached is not None:
        return cached

    # 3. 获取资金流向数据（AkShare）
    market = _get_market(stock_code)
    max_retries = 3
    last_error = None
    df = None

    for attempt in range(max_retries):
        try:
            df = ak.stock_individual_fund_flow(stock=stock_code, market=market)
            break
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(1)
    else:
        raise ConnectionError(f"AkShare 资金流向接口失败（重试 {max_retries} 次）: {last_error}")

    if df is None or df.empty:
        raise ValueError(f"股票代码 '{stock_code}' 未查询到资金流向数据")

    # 4. 标准化列名
    df = _normalize_flow_columns(df)

    # 5. 获取实时行情（补充年最高价）
    stock_name, year_high = _fetch_realtime_quote(stock_code)

    # 6. 构造返回数据
    records = df.to_dict(orient="records")
    latest = records[-1] if records else {}

    # 计算高位风险
    current_price = latest.get("close", 0)
    if year_high and year_high > 0:
        vs_high_pct = round((1 - current_price / year_high) * 100, 2)
        near_high = vs_high_pct < 10  # 距离年内高点不到 10% 视为高位预警
    else:
        vs_high_pct = None
        near_high = False

    result = {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "latest": latest,
        "flow_trend": records,
        "risk": {
            "year_high": year_high,
            "current_vs_high_pct": vs_high_pct,
            "near_high_warning": near_high,
        },
    }

    _set_cache(stock_code, result)
    return result


def _normalize_flow_columns(df: pd.DataFrame) -> pd.DataFrame:
    """标准化资金流向列名"""
    col_map = {}
    for col in df.columns:
        col_str = str(col).strip()
        if "日期" in col_str:
            col_map[col] = "date"
        elif "收盘价" in col_str:
            col_map[col] = "close"
        elif "涨跌幅" in col_str and "净占比" not in col_str:
            col_map[col] = "pct_change"
        elif "主力净流入-净额" in col_str:
            col_map[col] = "main_net_inflow"
        elif "主力净流入-净占比" in col_str:
            col_map[col] = "main_net_ratio"
        elif "超大单净流入-净额" in col_str:
            col_map[col] = "super_big_net_inflow"
        elif "超大单净流入-净占比" in col_str:
            col_map[col] = "super_big_net_ratio"
        elif "大单净流入-净额" in col_str:
            col_map[col] = "big_net_inflow"
        elif "大单净流入-净占比" in col_str:
            col_map[col] = "big_net_ratio"
        elif "中单净流入-净额" in col_str:
            col_map[col] = "mid_net_inflow"
        elif "小单净流入-净额" in col_str:
            col_map[col] = "small_net_inflow"

    df = df.rename(columns=col_map)

    # 数值列转换
    numeric_cols = ["close", "pct_change", "main_net_inflow", "main_net_ratio",
                    "super_big_net_inflow", "super_big_net_ratio",
                    "big_net_inflow", "big_net_ratio", "mid_net_inflow", "small_net_inflow"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _fetch_realtime_quote(stock_code: str) -> tuple:
    """
    从新浪接口获取实时行情，返回 (股票名称, 年内最高价)
    """
    sina_symbol = _get_sina_symbol(stock_code)
    try:
        r = requests.get(
            f"{SINA_QUOTE_URL}{sina_symbol}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        r.encoding = "gbk"
        fields = r.text.split("~")
        if len(fields) > 47:
            name = fields[1]  # 股票名称
            year_high = float(fields[47]) if fields[47] else 0  # 年内最高
            return name, year_high
    except Exception:
        pass
    return "", 0
