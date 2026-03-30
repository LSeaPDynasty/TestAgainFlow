"""
请求上下文中间件 - 为每个请求添加追踪信息
"""
import uuid
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """请求上下文中间件，为每个请求添加追踪信息"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成唯一的请求ID
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # 添加请求上下文信息
        request.state.request_id = request_id
        request.state.start_time = start_time

        # 从请求中提取用户信息（如果已认证）
        user_id = None
        username = None
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # 这里可以添加JWT解析逻辑获取用户信息
                # 暂时设置为None，由认证中间件设置
                pass
        except Exception:
            pass

        request.state.user_id = user_id
        request.state.username = username

        # 记录请求开始
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "user_id": user_id,
                "client_host": request.client.host if request.client else None,
            }
        )

        try:
            # 处理请求
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            # 记录请求完成
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "user_id": user_id,
                }
            )

            return response

        except Exception as exc:
            # 记录未捕获的异常
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": process_time,
                    "user_id": user_id,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                },
                exc_info=True
            )
            raise