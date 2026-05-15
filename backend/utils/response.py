"""
统一 JSON 响应格式 - Pydantic 模型版
标准格式: {"code": 200, "data": {}, "msg": "success"}
"""
from typing import Any, Optional
from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一 API 响应模型"""
    code: int = 200
    data: Optional[Any] = None
    msg: str = "success"


def success(data: Any = None, msg: str = "success") -> dict:
    """成功响应"""
    return ApiResponse(code=200, data=data, msg=msg).model_dump()


def error(msg: str = "error", code: int = 500) -> dict:
    """错误响应"""
    return ApiResponse(code=code, data=None, msg=msg).model_dump()
