"""
Custom exceptions
"""


class AppError(Exception):
    """Base application error"""
    def __init__(self, message: str, code: int = 5000):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NotFoundError(AppError):
    """Resource not found error"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code=ErrorCode.NOT_FOUND)


class ConflictError(AppError):
    """Resource conflict error"""
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, code=ErrorCode.CONFLICT)


class DependencyError(AppError):
    """Dependency error - cannot delete due to references"""
    def __init__(self, message: str = "Resource has dependencies"):
        super().__init__(message, code=ErrorCode.DEPENDENCY_ERROR)


class ValidationError(AppError):
    """Validation error"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, code=ErrorCode.VALIDATION_ERROR)


from .response import ErrorCode
