"""
ETF 数据服务 - 核心业务逻辑

数据源: 新浪财经 K 线 API（东方财富接口在国内部分网络环境不可达，改用新浪）
功能:
1. 获取 ETF 近一年历史净值数据
2. 基于历史价格计算当前估值百分位
3. 返回标准格式的 JSON 数据
"""
import time
import requests
import pandas as pd

# 缓存: 避免频繁请求同一 ETF 数据
# key = etf_code, value = {"data": DataFrame, "time": timestamp}
_cache: dict = {}
CACHE_TTL = 300  # 缓存有效期 5 分钟

# 新浪历史 K 线接口
SINA_KLINE_URL = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.sina.com.cn",
}


def _validate_etf_code(code: str) -> bool:
    """
    校验 ETF 代码格式
    合法格式: 6 位纯数字，以 5/1 开头（场内 ETF 常见前缀）
    """
    if not code or not code.isdigit() or len(code) != 6:
        return False
    return code.startswith(("5", "1"))


def _code_to_sina_symbol(code: str) -> str:
    """
    ETF 代码转新浪行情代码
    5xxxxx → sh5xxxxx (上海)
    1xxxxx → sz1xxxxx (深圳)
    """
    if code.startswith("5"):
        return f"sh{code}"
    else:
        return f"sz{code}"


def _get_cached(code: str) -> pd.DataFrame | None:
    """从缓存获取数据，过期则返回 None"""
    if code in _cache:
        entry = _cache[code]
        if time.time() - entry["time"] < CACHE_TTL:
            return entry["data"]
    return None


def _set_cache(code: str, data: pd.DataFrame):
    """写入缓存"""
    _cache[code] = {"data": data, "time": time.time()}


def fetch_etf_history(etf_code: str) -> dict:
    """
    获取指定 ETF 近一年历史净值

    Args:
        etf_code: ETF 代码，如 "512010"

    Returns:
        标准 JSON 格式:
        {
            "code": 200,
            "data": {
                "etf_code": "512010",
                "records": [{"date": "2025-05-15", "close": 0.412, ...}, ...],
                "summary": {"latest_date": "...", "latest_close": ..., "year_high": ..., "year_low": ...}
            },
            "msg": "success"
        }

    Raises:
        ValueError: ETF 代码格式错误或无数据
        ConnectionError: 网络请求失败
    """
    # 1. 校验 ETF 代码
    if not _validate_etf_code(etf_code):
        raise ValueError(
            f"ETF 代码格式错误: '{etf_code}'，应为 6 位数字且以 5 或 1 开头"
        )

    # 2. 检查缓存
    cached = _get_cached(etf_code)
    if cached is not None:
        return _build_result(etf_code, cached)

    # 3. 调用新浪 K 线 API（近一年，约 250 个交易日）
    sina_symbol = _code_to_sina_symbol(etf_code)
    params = {
        "symbol": sina_symbol,
        "scale": "240",   # 日K = 240 分钟
        "ma": "no",
        "datalen": "250", # 近 250 个交易日
    }

    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            r = requests.get(
                SINA_KLINE_URL,
                params=params,
                headers=REQUEST_HEADERS,
                timeout=15,
            )
            r.raise_for_status()
            raw_data = r.json()
            break
        except requests.exceptions.Timeout:
            last_error = "请求超时"
        except requests.exceptions.ConnectionError:
            last_error = "网络连接失败"
        except Exception as e:
            last_error = str(e)

        if attempt < max_retries - 1:
            time.sleep(1)
    else:
        raise ConnectionError(f"新浪行情接口请求失败（重试 {max_retries} 次）: {last_error}")

    # 4. 校验返回数据
    if not raw_data:
        raise ValueError(f"ETF 代码 '{etf_code}' 未查询到历史数据")

    # 5. 转为 DataFrame
    df = pd.DataFrame(raw_data)

    # 6. 标准化列名和数据类型
    df = _normalize_columns(df)

    # 7. 写入缓存
    _set_cache(etf_code, df)

    return _build_result(etf_code, df)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    标准化列名

    新浪 API 返回: day, open, high, low, close, volume
    映射为:        date, open, high, low, close, volume
    """
    # 新浪返回的列名本身就是英文，只需处理 day → date
    if "day" in df.columns:
        df = df.rename(columns={"day": "date"})

    # 数值列转为 float
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _build_result(etf_code: str, df: pd.DataFrame) -> dict:
    """
    构造标准返回数据

    包含:
    - records: 完整历史记录列表
    - summary: 最新价、年内最高/最低、估值百分位
    """
    records = df.to_dict(orient="records")

    close_series = df["close"].dropna()
    latest_close = float(close_series.iloc[-1]) if len(close_series) > 0 else 0

    summary = {
        "latest_date": df["date"].iloc[-1] if len(df) > 0 else "",
        "latest_close": round(latest_close, 4),
        "year_high": round(float(close_series.max()), 4),
        "year_low": round(float(close_series.min()), 4),
        "percentile": _calc_percentile(close_series),
    }

    return {
        "etf_code": etf_code,
        "records": records,
        "summary": summary,
    }


def _calc_percentile(series: pd.Series) -> float:
    """
    计算当前价格在近一年中的百分位

    百分位 = 当前价格在历史价格中的排名比例
    例如: 百分位 80% 表示当前价格高于近一年 80% 的时间

    Args:
        series: 近一年每日收盘价序列

    Returns:
        百分位数值 (0-100)，保留两位小数
    """
    if len(series) < 2:
        return 0.0

    current = series.iloc[-1]
    percentile = (series < current).sum() / len(series) * 100
    return round(float(percentile), 2)
