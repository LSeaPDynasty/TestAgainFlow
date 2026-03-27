"""
Executor Capability Registration Service
"""
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.executor import Executor, ActionType, ExecutorActionCapability
from app.schemas.executor import (
    ExecutorRegistrationRequest,
    ExecutorRegistrationResponse,
    ActionTypeResponse,
    ActionTypesResponse,
    ActionCapabilityCheckResponse,
    TestcaseValidationResponse,
)

logger = logging.getLogger(__name__)


class ExecutorCapabilityService:
    """执行器能力注册服务"""

    def __init__(self, db: Session):
        self.db = db

    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        比较两个版本号

        Returns:
            -1: version1 < version2
             0: version1 == version2
             1: version1 > version2
        """
        def normalize_version(v):
            # 移除 'v' 前缀，分割成数字列表
            v = v.lstrip('vV')
            parts = v.split('.')
            # 补齐到3位
            while len(parts) < 3:
                parts.append('0')
            return [int(p) if p.isdigit() else 0 for p in parts[:3]]

        v1_parts = normalize_version(version1)
        v2_parts = normalize_version(version2)

        if v1_parts < v2_parts:
            return -1
        elif v1_parts > v2_parts:
            return 1
        else:
            return 0

    def register_executor(self, req: ExecutorRegistrationRequest) -> ExecutorRegistrationResponse:
        """
        注册执行器及其能力

        策略：
        - Executor: 更新或创建
        - ActionTypes: 只增不减，累积所有见过的类型
        - Capabilities: 重建该执行器的能力列表
        """
        try:
            # 1. 查找或创建执行器
            executor = self.db.query(Executor).filter(
                Executor.executor_id == req.executor_id
            ).first()

            if executor:
                # 更新现有执行器
                executor.executor_version = req.executor_version
                executor.hostname = req.hostname
                executor.ip_address = req.ip_address
                executor.last_seen = datetime.utcnow()
                executor.is_online = True
                logger.info(f"更新执行器: {req.executor_id} v{req.executor_version}")
            else:
                # 创建新执行器
                executor = Executor(
                    executor_id=req.executor_id,
                    executor_version=req.executor_version,
                    hostname=req.hostname,
                    ip_address=req.ip_address,
                    is_online=True,
                )
                self.db.add(executor)
                logger.info(f"注册新执行器: {req.executor_id} v{req.executor_version}")

            self.db.flush()  # 确保executor有ID

            # 2. 处理操作类型（只增不减）
            new_actions_count = 0
            action_type_map = {}

            for action_req in req.capabilities:
                # 查找或创建操作类型
                action_type = self.db.query(ActionType).filter(
                    ActionType.type_code == action_req.type_code
                ).first()

                if not action_type:
                    # 新操作类型，创建
                    action_type = ActionType(
                        type_code=action_req.type_code,
                        display_name=action_req.display_name,
                        category=action_req.category,
                        description=action_req.description,
                        color=action_req.color,
                        requires_element=action_req.requires_element,
                        requires_value=action_req.requires_value,
                        config_schema=json.dumps(action_req.config_schema or {}, ensure_ascii=False),
                        first_seen_executor_id=req.executor_id,
                    )
                    self.db.add(action_type)
                    new_actions_count += 1
                    logger.info(f"新操作类型: {action_req.type_code} - {action_req.display_name}")
                else:
                    # 操作类型已存在，检查版本号
                    # 查询支持该操作类型的所有在线引擎，找出最新版本
                    from sqlalchemy import desc
                    latest_capability = self.db.query(ExecutorActionCapability).filter(
                        ExecutorActionCapability.action_type_code == action_req.type_code
                    ).order_by(
                        desc(ExecutorActionCapability.executor_version)
                    ).first()

                    current_latest_version = latest_capability.executor_version if latest_capability else "0.0.0"
                    new_version = req.executor_version

                    # 比较版本号
                    if self._compare_versions(new_version, current_latest_version) >= 0:
                        # 新版本相同或更高，允许更新
                        action_type.display_name = action_req.display_name
                        action_type.category = action_req.category
                        action_type.description = action_req.description
                        if action_req.color:
                            action_type.color = action_req.color
                        action_type.config_schema = json.dumps(action_req.config_schema or {}, ensure_ascii=False)
                        action_type.requires_element = action_req.requires_element
                        action_type.requires_value = action_req.requires_value
                        logger.info(f"更新操作类型: {action_req.type_code} (版本 {current_latest_version} -> {new_version})")
                    else:
                        # 旧版本引擎，跳过更新
                        logger.warning(
                            f"忽略旧版本引擎的操作更新: {action_req.type_code} "
                            f"(当前最新版本: {current_latest_version}, 请求版本: {new_version})"
                        )

                self.db.flush()
                action_type_map[action_req.type_code] = action_type

            # 3. 重建该执行器的能力关联（先删后建）
            self.db.query(ExecutorActionCapability).filter(
                ExecutorActionCapability.executor_id == req.executor_id
            ).delete()

            for action_req in req.capabilities:
                action_type = action_type_map.get(action_req.type_code)
                if action_type:
                    capability = ExecutorActionCapability(
                        executor_id=req.executor_id,
                        action_type_code=action_req.type_code,
                        executor_version=req.executor_version,
                        implementation_version=action_req.implementation_version or "1.0",
                    )
                    self.db.add(capability)

            self.db.commit()

            return ExecutorRegistrationResponse(
                executor_id=req.executor_id,
                registered=True,
                new_actions_count=new_actions_count,
                total_actions_count=len(req.capabilities),
                message=f"执行器 {req.executor_id} 注册成功，发现 {new_actions_count} 个新操作类型"
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"注册执行器失败: {e}", exc_info=True)
            raise

    def heartbeat(self, executor_id: str, executor_version: Optional[str] = None):
        """执行器心跳"""
        executor = self.db.query(Executor).filter(
            Executor.executor_id == executor_id
        ).first()

        if executor:
            executor.last_seen = datetime.utcnow()
            executor.is_online = True
            if executor_version:
                executor.executor_version = executor_version
            self.db.commit()
            logger.debug(f"执行器心跳: {executor_id}")
        else:
            logger.warning(f"未知的执行器心跳: {executor_id}")

    def get_all_action_types(self, include_deprecated: bool = False) -> ActionTypesResponse:
        """获取所有操作类型"""
        from datetime import datetime

        query = self.db.query(ActionType)
        if not include_deprecated:
            query = query.filter(ActionType.is_deprecated == False)

        action_types = query.order_by(ActionType.category, ActionType.display_name).all()

        # 构建响应
        items = []
        categories = {}

        for at in action_types:
            # 查询支持此操作类型的执行器
            capabilities = self.db.query(ExecutorActionCapability).filter(
                and_(
                    ExecutorActionCapability.action_type_code == at.type_code,
                    ExecutorActionCapability.executor_id.in_(
                        self.db.query(Executor.executor_id).filter(Executor.is_online == True)
                    )
                )
            ).all()

            supported_by = [c.executor_id for c in capabilities]

            # 解析config_schema JSON
            config_schema = {}
            if at.config_schema:
                try:
                    config_schema = json.loads(at.config_schema)
                except Exception as e:
                    logger.warning(f"Failed to parse config_schema for {at.type_code}: {e}")
                    config_schema = {}

            item = ActionTypeResponse(
                id=at.id,
                type_code=at.type_code,
                display_name=at.display_name,
                category=at.category or "未分类",
                description=at.description,
                color=at.color,
                requires_element=at.requires_element,
                requires_value=at.requires_value,
                config_schema=config_schema,
                first_seen_executor_id=at.first_seen_executor_id,
                first_seen_at=at.first_seen_at or datetime.utcnow(),
                is_deprecated=at.is_deprecated,
                created_at=at.created_at,
                updated_at=at.updated_at,
                supported_by_executors=supported_by,
            )
            items.append(item)

            # 按分类分组
            cat = at.category or "未分类"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(at.type_code)

        return ActionTypesResponse(
            total=len(items),
            items=items,
            categories=categories,
        )

    def check_capability(
        self,
        action_types: List[str],
        executor_id: Optional[str] = None
    ) -> ActionCapabilityCheckResponse:
        """检查操作能力是否支持"""
        # 获取目标执行器
        if executor_id:
            executors = self.db.query(Executor).filter(
                and_(
                    Executor.executor_id == executor_id,
                    Executor.is_online == True
                )
            ).all()
        else:
            # 所有在线执行器
            executors = self.db.query(Executor).filter(
                Executor.is_online == True
            ).all()

        if not executors:
            return ActionCapabilityCheckResponse(
                is_supported=False,
                executor_id=executor_id,
                supported_actions=[],
                unsupported_actions=action_types,
                can_execute=False,
                warnings=["没有可用的在线执行器"]
            )

        # 检查第一个执行器的能力
        target_executor = executors[0]
        capabilities = self.db.query(ExecutorActionCapability).filter(
            ExecutorActionCapability.executor_id == target_executor.executor_id
        ).all()

        supported_codes = {c.action_type_code for c in capabilities}

        supported = [at for at in action_types if at in supported_codes]
        unsupported = [at for at in action_types if at not in supported_codes]

        can_execute = len(unsupported) == 0
        warnings = []
        if unsupported:
            warnings.append(f"执行器 {target_executor.executor_id} 不支持以下操作: {', '.join(unsupported)}")

        return ActionCapabilityCheckResponse(
            is_supported=can_execute,
            executor_id=target_executor.executor_id,
            supported_actions=supported,
            unsupported_actions=unsupported,
            can_execute=can_execute,
            warnings=warnings
        )

    def validate_testcase(
        self,
        testcase_id: int,
        executor_id: Optional[str] = None,
        skip_unsupported: bool = False
    ) -> TestcaseValidationResponse:
        """验证用例是否可以在指定执行器上执行"""
        from app.models.testcase import Testcase
        from app.models.testcase_item import TestcaseItem

        # 获取用例及其所有步骤
        testcase = self.db.query(Testcase).filter(Testcase.id == testcase_id).first()
        if not testcase:
            raise ValueError(f"用例不存在: {testcase_id}")

        # 收集用例中的所有操作类型
        action_types = set()

        # 从testcase_flows中收集（旧格式）
        for tf in testcase.testcase_flows:
            flow = tf.flow
            if flow:
                for fs in flow.flow_steps:
                    step = fs.step
                    if step:
                        action_types.add(step.action_type)

        # 从inline_steps中收集
        for step in testcase.inline_steps:
            action_types.add(step.action_type)

        # 从testcase_items中收集（新格式：flow/step混排）
        testcase_items = self.db.query(TestcaseItem).filter(
            TestcaseItem.testcase_id == testcase_id
        ).all()

        for item in testcase_items:
            if item.item_type == 'flow' and item.flow:
                # Flow类型，获取flow的所有steps
                for fs in item.flow.flow_steps:
                    if fs.step:
                        action_types.add(fs.step.action_type)
            elif item.item_type == 'step' and item.step:
                # Step类型，直接获取step
                action_types.add(item.step.action_type)

        action_type_list = list(action_types)

        # 检查能力
        check_result = self.check_capability(action_type_list, executor_id)

        # 构建不支持的详细信息
        unsupported_details = []
        for at in check_result.unsupported_actions:
            # 统计不支持的步骤数（简化统计）
            unsupported_details.append({
                "action_type": at,
                "step_count": 0,  # TODO: 可以改进统计
            })

        # 生成建议
        if check_result.can_execute:
            recommendation = "用例可以在执行器上正常执行"
        elif skip_unsupported:
            recommendation = "建议：跳过此用例或升级执行器版本"
        else:
            recommendation = "建议：升级执行器版本或移除不支持的操作"

        return TestcaseValidationResponse(
            testcase_id=testcase_id,
            testcase_name=testcase.name,
            can_execute=check_result.can_execute,
            executor_id=check_result.executor_id,
            all_actions_supported=check_result.can_execute,
            unsupported_actions=unsupported_details,
            warnings=check_result.warnings,
            recommendation=recommendation
        )


# 导入datetime
from datetime import datetime
