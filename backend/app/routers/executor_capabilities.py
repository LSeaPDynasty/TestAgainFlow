"""
Executor Capability Registration API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.executor import (
    ExecutorRegistrationRequest,
    ExecutorRegistrationResponse,
    ActionTypesResponse,
    ActionCapabilityCheckRequest,
    ActionCapabilityCheckResponse,
    TestcaseValidationRequest,
    TestcaseValidationResponse,
)
from app.schemas.common import ApiResponse
from app.services.executor_capability_service import ExecutorCapabilityService
from app.utils.response import ok, error

router = APIRouter(prefix="/executor-capabilities", tags=["executor-capabilities"])


@router.post("/register", response_model=ApiResponse[ExecutorRegistrationResponse])
def register_executor(
    req: ExecutorRegistrationRequest,
    db: Session = Depends(get_db_session)
):
    """
    执行器注册接口

    执行器启动时调用此接口，注册自己的能力和支持的操作类型。

    **策略：**
    - 执行器：更新或创建
    - 操作类型：只增不减，累积所有见过的类型
    - 能力关联：重建该执行器的能力列表

    **请求示例：**
    ```json
    {
        "executor_id": "executor-pixel5-001",
        "executor_version": "1.0.0",
        "hostname": "test-machine-01",
        "ip_address": "192.168.1.100",
        "capabilities": [
            {
                "type_code": "click",
                "display_name": "点击",
                "category": "设备操作",
                "description": "点击屏幕元素",
                "color": "blue",
                "requires_element": true,
                "requires_value": false,
                "implementation_version": "1.0"
            },
            {
                "type_code": "screenshot",
                "display_name": "截图",
                "category": "系统",
                "description": "截取设备屏幕",
                "color": "gold",
                "requires_element": false,
                "requires_value": false,
                "implementation_version": "1.0"
            }
        ]
    }
    ```
    """
    try:
        service = ExecutorCapabilityService(db)
        result = service.register_executor(req)
        return ok(data=result, message=result.message)
    except Exception as e:
        return error(code=500, message=f"注册失败: {str(e)}")


@router.post("/heartbeat", response_model=ApiResponse[dict])
def executor_heartbeat(
    req: dict,
    db: Session = Depends(get_db_session)
):
    """
    执行器心跳接口

    执行器定期调用此接口，保持在线状态。

    **请求示例：**
    ```json
    {
        "executor_id": "executor-pixel5-001",
        "executor_version": "1.0.0"
    }
    ```
    """
    executor_id = req.get("executor_id")
    executor_version = req.get("executor_version")

    if not executor_id:
        return error(code=400, message="缺少executor_id")

    try:
        service = ExecutorCapabilityService(db)
        service.heartbeat(executor_id, executor_version)
        return ok(data={"status": "ok"}, message="心跳成功")
    except Exception as e:
        return error(code=500, message=f"心跳失败: {str(e)}")


@router.get("/action-types", response_model=ApiResponse[ActionTypesResponse])
def get_action_types(
    include_deprecated: bool = Query(False, description="是否包含已废弃的操作类型"),
    db: Session = Depends(get_db_session)
):
    """
    获取所有操作类型列表

    返回系统中所有已注册的操作类型，包括它们的分类、配置和支持的执行器。

    **响应示例：**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "total": 15,
            "items": [
                {
                    "type_code": "click",
                    "display_name": "点击",
                    "category": "设备操作",
                    "color": "blue",
                    "requires_element": true,
                    "supported_by_executors": ["executor-pixel5-001", "executor-pixel5-002"]
                }
            ],
            "categories": {
                "设备操作": ["click", "input", "swipe"],
                "等待": ["wait_element", "wait_time"],
                "断言": ["assert_text", "assert_exists"]
            }
        }
    }
    ```
    """
    try:
        service = ExecutorCapabilityService(db)
        result = service.get_all_action_types(include_deprecated=include_deprecated)
        return ok(data=result)
    except Exception as e:
        return error(code=500, message=f"获取操作类型失败: {str(e)}")


@router.post("/check-capability", response_model=ApiResponse[ActionCapabilityCheckResponse])
def check_capability(
    req: ActionCapabilityCheckRequest,
    db: Session = Depends(get_db_session)
):
    """
    检查操作能力是否支持

    检查指定的操作类型是否在执行器支持范围内。

    **请求示例：**
    ```json
    {
        "executor_id": "executor-pixel5-001",
        "action_types": ["click", "input", "screenshot", "custom_action"]
    }
    ```

    **响应示例：**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "is_supported": true,
            "executor_id": "executor-pixel5-001",
            "supported_actions": ["click", "input", "screenshot"],
            "unsupported_actions": ["custom_action"],
            "can_execute": false,
            "warnings": ["执行器不支持以下操作: custom_action"]
        }
    }
    ```
    """
    try:
        service = ExecutorCapabilityService(db)
        result = service.check_capability(req.action_types, req.executor_id)
        return ok(data=result)
    except Exception as e:
        return error(code=500, message=f"检查能力失败: {str(e)}")


@router.post("/validate-testcase", response_model=ApiResponse[TestcaseValidationResponse])
def validate_testcase(
    req: TestcaseValidationRequest,
    db: Session = Depends(get_db_session)
):
    """
    验证用例是否可以在执行器上执行

    在执行用例前，检查用例中的所有操作是否都被执行器支持。

    **请求示例：**
    ```json
    {
        "testcase_id": 123,
        "executor_id": "executor-pixel5-001",
        "skip_unsupported": false
    }
    ```

    **响应示例：**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "testcase_id": 123,
            "testcase_name": "用户登录测试",
            "can_execute": true,
            "executor_id": "executor-pixel5-001",
            "all_actions_supported": true,
            "unsupported_actions": [],
            "warnings": [],
            "recommendation": "用例可以在执行器上正常执行"
        }
    }
    ```
    """
    try:
        service = ExecutorCapabilityService(db)
        result = service.validate_testcase(
            req.testcase_id,
            req.executor_id,
            req.skip_unsupported
        )
        return ok(data=result)
    except ValueError as e:
        return error(code=404, message=str(e))
    except Exception as e:
        return error(code=500, message=f"验证用例失败: {str(e)}")
