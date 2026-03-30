"""
Utils package - utility functions and helpers
"""
from .response import ok, error, ErrorCode
from .exceptions import NotFoundError, ConflictError, DependencyError
from .pagination import get_pagination_params
from .dsl_parser import DslParser
from .context_builder import build_execution_context
from .cache import cache, cached, cache_result, MemoryCache
from .adb import (
    run_adb_command,
    get_adb_devices,
    check_device_online,
    get_device_info,
    find_element,
    tap_element,
    input_text,
    press_back,
    take_screenshot,
    start_activity
)

__all__ = [
    'ok',
    'error',
    'ErrorCode',
    'NotFoundError',
    'ConflictError',
    'DependencyError',
    'get_pagination_params',
    'DslParser',
    'build_execution_context',
    'cache',
    'cached',
    'cache_result',
    'MemoryCache',
    'run_adb_command',
    'get_adb_devices',
    'check_device_online',
    'get_device_info',
    'find_element',
    'tap_element',
    'input_text',
    'press_back',
    'take_screenshot',
    'start_activity',
]
