"""
统一错误处理中间件
"""
import logging
import traceback
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.utils.response import error

logger = logging.getLogger(__name__)


class AppException(Exception):
    """应用基础异常类"""

    def __init__(
        self,
        message: str,
        code: int = status.HTTP_400_BAD_REQUEST,
        details: Union[dict, None] = None
    ):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class NotFoundException(AppException):
    """资源未找到异常"""

    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(message, status.HTTP_404_NOT_FOUND, details)


class ConflictException(AppException):
    """资源冲突异常"""

    def __init__(self, message: str = "Resource conflict", details: dict = None):
        super().__init__(message, status.HTTP_409_CONFLICT, details)


class BadRequestException(AppException):
    """错误请求异常"""

    def __init__(self, message: str = "Bad request", details: dict = None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)


class UnauthorizedException(AppException):
    """未授权异常"""

    def __init__(self, message: str = "Unauthorized", details: dict = None):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, details)


class ForbiddenException(AppException):
    """禁止访问异常"""

    def __init__(self, message: str = "Forbidden", details: dict = None):
        super().__init__(message, status.HTTP_403_FORBIDDEN, details)


class ValidationException(AppException):
    """验证异常"""

    def __init__(self, message: str = "Validation failed", details: dict = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class InternalServerException(AppException):
    """服务器内部错误异常"""

    def __init__(self, message: str = "Internal server error", details: dict = None):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """处理应用自定义异常"""
    # 获取请求上下文
    request_id = getattr(request.state, 'request_id', 'N/A')
    user_id = getattr(request.state, 'user_id', None)
    username = getattr(request.state, 'username', None)

    # 根据HTTP状态码决定日志级别
    log_level = logger.error if exc.code >= 500 else logger.warning
    log_level(
        f"AppException: {exc.code} - {exc.message}",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "username": username,
            "path": request.url.path,
            "method": request.method,
            "exception_code": exc.code,
            "exception_message": exc.message,
        }
    )

    return JSONResponse(
        status_code=exc.code,
        content=error(message=exc.message, code=exc.code, data=exc.details)
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """处理Pydantic验证异常"""
    errors = exc.errors()
    logger.warning(f"Validation error: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error(
            message="Validation failed",
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            data={"errors": errors}
        )
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """处理SQLAlchemy数据库异常"""
    logger.error(f"Database error: {str(exc)}")

    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=error(message="Database integrity error", code=status.HTTP_409_CONFLICT)
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error(message="Database error occurred", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理所有未捕获的异常"""
    # 获取请求上下文
    request_id = getattr(request.state, 'request_id', 'N/A')
    user_id = getattr(request.state, 'user_id', None)
    username = getattr(request.state, 'username', None)

    # 记录基本异常信息，包含请求上下文
    logger.error(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "username": username,
            "path": request.url.path,
            "method": request.method,
            "exc_type": type(exc).__name__,
            "exc_message": str(exc),
        }
    )

    # 在开发环境记录详细堆栈，生产环境不记录
    import os
    if os.getenv("DEBUG", "false").lower() == "true":
        logger.error(traceback.format_exc())
    else:
        # 生产环境只记录关键信息，过滤可能包含敏感数据的堆栈
        logger.error("Use debug mode to see detailed stack trace")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error(
            message="Internal server error",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    )


def setup_error_handlers(app):
    """设置统一的错误处理器"""
    from fastapi import FastAPI

    # 应用自定义异常
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Error handlers registered successfully")