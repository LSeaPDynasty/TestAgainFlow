"""Service helpers for testcase router."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.flow import Flow
from app.schemas.testcase import (
    DependencyChainFlowSchema,
    DependencyChainResponse,
    DependencyChainStepSchema,
    InlineStepSchema,
    TestcaseCreate,
    TestcaseDetailResponse,
    TestcaseFlowDetailSchema,
    TestcaseItemResponseSchema,
    TestcaseResponse,
    TestcaseUpdate,
    TagSchema,
)

VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}


@dataclass
class ServiceValidationError:
    code: int
    message: str


def parse_priority(priority: Optional[str]) -> Optional[list[str]]:
    if not priority:
        return None
    return [p.strip() for p in priority.split(",") if p.strip()]


def parse_tag_ids(tag_id: Optional[int], tag_ids: Optional[str]) -> Optional[list[int]]:
    tag_source = tag_ids if tag_ids else (str(tag_id) if tag_id else None)
    if not tag_source:
        return None
    return [int(t) for t in tag_source.split(",") if t.strip().isdigit()]


def list_testcases(
    db: Session,
    *,
    skip: int,
    limit: int,
    search: Optional[str],
    priority: Optional[str],
    tag_id: Optional[int],
    tag_ids: Optional[str],
    project_id: Optional[int],
):
    from app.repositories.testcase_repo import TestcaseRepository

    repo = TestcaseRepository(db)
    return repo.list_with_details(
        skip=skip,
        limit=limit,
        search=search,
        priority=parse_priority(priority),
        tag_ids=parse_tag_ids(tag_id, tag_ids),
        project_id=project_id,
    )


def get_testcase_detail(db: Session, testcase_id: int):
    from app.repositories.testcase_repo import TestcaseRepository

    repo = TestcaseRepository(db)
    testcase = repo.get_with_flows(testcase_id)
    if not testcase:
        return None
    return build_testcase_detail_response(db, testcase)


def validate_testcase_create(
    *,
    testcase_in: TestcaseCreate,
    testcase_repo,
    flow_repo,
    db: Session,
) -> Optional[ServiceValidationError]:
    if not testcase_in.name or not testcase_in.name.strip():
        return ServiceValidationError(code=4001, message="Testcase name cannot be empty")
    if testcase_in.priority not in VALID_PRIORITIES:
        return ServiceValidationError(
            code=4001,
            message=f"Invalid priority: {testcase_in.priority}. Must be one of: P0, P1, P2, P3",
        )
    if testcase_repo.get_by_name(testcase_in.name):
        return ServiceValidationError(code=4009, message="Testcase name already exists")

    # 验证：testcase 必须有可执行的内容
    # 可以是：main_flows, inline_steps, 或者稍后通过 testcase_items API 添加
    has_main_flows = testcase_in.main_flows and len(testcase_in.main_flows) > 0
    has_inline_steps = testcase_in.inline_steps and len(testcase_in.inline_steps) > 0

    # 如果既没有 main_flows 也没有 inline_steps，允许创建（testcase_items 可以稍后添加）
    # 这样前端可以创建一个"空壳"testcase，然后再添加 testcase_items
    # 注意：testcase_items 是通过单独的 API 端点创建的，不在创建时验证

    for tf in (testcase_in.main_flows or []):
        if not flow_repo.get(tf.flow_id):
            return ServiceValidationError(code=4004, message=f"Flow not found: flow_id={tf.flow_id}")
    for tf in (testcase_in.setup_flows or []) + (testcase_in.teardown_flows or []):
        if not flow_repo.get(tf.flow_id):
            return ServiceValidationError(code=4004, message=f"Flow not found: flow_id={tf.flow_id}")

    if testcase_in.inline_steps:
        from app.repositories.step_repo import StepRepository

        step_repo = StepRepository(db)
        for inline_step in testcase_in.inline_steps:
            if not step_repo.get(inline_step.step_id):
                return ServiceValidationError(
                    code=4004, message=f"Step not found: step_id={inline_step.step_id}"
                )
    return None


def build_create_payload(testcase_in: TestcaseCreate) -> dict:
    testcase_data = testcase_in.model_dump(
        exclude={"tag_ids", "setup_flows", "main_flows", "teardown_flows", "inline_steps"}
    )
    return {
        **testcase_data,
        "tag_ids": testcase_in.tag_ids,
        "setup_flows": [tf.model_dump() for tf in testcase_in.setup_flows] if testcase_in.setup_flows and len(testcase_in.setup_flows) > 0 else [],
        "main_flows": [tf.model_dump() for tf in testcase_in.main_flows] if testcase_in.main_flows and len(testcase_in.main_flows) > 0 else [],
        "teardown_flows": [tf.model_dump() for tf in testcase_in.teardown_flows]
        if testcase_in.teardown_flows and len(testcase_in.teardown_flows) > 0
        else [],
        "inline_steps": [is_.model_dump() for is_ in testcase_in.inline_steps]
        if testcase_in.inline_steps and len(testcase_in.inline_steps) > 0 else [],
    }


def build_update_payload(testcase_in: TestcaseUpdate) -> dict:
    update_data = {
        k: v
        for k, v in testcase_in.model_dump().items()
        if v is not None and k not in ["tag_ids", "setup_flows", "main_flows", "teardown_flows", "inline_steps"]
    }
    return {
        **update_data,
        "tag_ids": testcase_in.tag_ids,
        "setup_flows": [tf.model_dump() for tf in testcase_in.setup_flows]
        if testcase_in.setup_flows and len(testcase_in.setup_flows) > 0
        else None,
        "main_flows": [tf.model_dump() for tf in testcase_in.main_flows]
        if testcase_in.main_flows and len(testcase_in.main_flows) > 0
        else None,
        "teardown_flows": [tf.model_dump() for tf in testcase_in.teardown_flows]
        if testcase_in.teardown_flows and len(testcase_in.teardown_flows) > 0
        else None,
        "inline_steps": [is_.model_dump() for is_ in testcase_in.inline_steps]
        if testcase_in.inline_steps and len(testcase_in.inline_steps) > 0
        else None,
    }


def create_testcase(db: Session, testcase_in: TestcaseCreate):
    from app.repositories.flow_repo import FlowRepository
    from app.repositories.testcase_repo import TestcaseRepository

    repo = TestcaseRepository(db)
    flow_repo = FlowRepository(db)

    validation = validate_testcase_create(
        testcase_in=testcase_in,
        testcase_repo=repo,
        flow_repo=flow_repo,
        db=db,
    )
    if validation:
        return None, validation

    testcase = repo.create_with_flows(build_create_payload(testcase_in))
    return build_testcase_response(testcase), None


def update_testcase(db: Session, testcase_id: int, testcase_in: TestcaseUpdate):
    from app.repositories.testcase_repo import TestcaseRepository

    repo = TestcaseRepository(db)
    testcase = repo.get(testcase_id)
    if not testcase:
        return None, ServiceValidationError(code=4004, message="Testcase not found")

    if testcase_in.name and testcase_in.name != testcase.name:
        if repo.get_by_name(testcase_in.name):
            return None, ServiceValidationError(code=4009, message="Testcase name already exists")

    updated = repo.update_with_flows(testcase_id, build_update_payload(testcase_in))
    return build_testcase_response(updated), None


def delete_testcase(db: Session, testcase_id: int):
    from app.repositories.testcase_repo import TestcaseRepository

    repo = TestcaseRepository(db)
    suite_count = repo.check_suite_usage(testcase_id)
    if suite_count > 0:
        return ServiceValidationError(code=4022, message="Testcase is referenced by suites"), {
            "referenced_by_suites_count": suite_count
        }

    if not repo.delete(testcase_id):
        return ServiceValidationError(code=4004, message="Testcase not found"), None

    return None, None


def duplicate_testcase(db: Session, testcase_id: int, new_name: str):
    from app.repositories.testcase_repo import TestcaseRepository

    repo = TestcaseRepository(db)
    if repo.get_by_name(new_name):
        return None, ServiceValidationError(code=4009, message="Testcase name already exists")

    new_testcase = repo.duplicate(testcase_id, new_name)
    if not new_testcase:
        return None, ServiceValidationError(code=4004, message="Testcase not found")
    return build_testcase_response(new_testcase), None


def get_dependency_chain_for_testcase(db: Session, testcase_id: int):
    from app.repositories.testcase_repo import TestcaseRepository

    repo = TestcaseRepository(db)
    testcase = repo.get_with_flows(testcase_id)
    if not testcase:
        return None, ServiceValidationError(code=4004, message="Testcase not found")
    return build_dependency_chain(db, testcase), None


def build_testcase_response(testcase) -> TestcaseResponse:
    from app.models.testcase_item import TestcaseItem

    setup_flow_count = len([tf for tf in testcase.testcase_flows if tf.flow_role == "setup"])
    main_flow_count = len([tf for tf in testcase.testcase_flows if tf.flow_role == "main"])
    teardown_flow_count = len([tf for tf in testcase.testcase_flows if tf.flow_role == "teardown"])

    # Count testcase_items
    testcase_item_count = 0
    if hasattr(testcase, 'testcase_items') and testcase.testcase_items:
        testcase_item_count = len(testcase.testcase_items)

    return TestcaseResponse(
        id=testcase.id,
        name=testcase.name,
        description=testcase.description,
        priority=testcase.priority,
        timeout=testcase.timeout,
        params=testcase.params,
        tags=[TagSchema(id=t.id, name=t.name) for t in testcase.tags],
        setup_flow_count=setup_flow_count,
        main_flow_count=main_flow_count,
        teardown_flow_count=teardown_flow_count,
        step_count=0,
        testcase_item_count=testcase_item_count,
        estimated_duration=0,
        suite_count=0,
        created_at=testcase.created_at,
        updated_at=testcase.updated_at,
    )


def build_testcase_detail_response(db: Session, testcase) -> TestcaseDetailResponse:
    from app.repositories.testcase_item_repo import TestcaseItemRepository

    flow_map = {flow.id: flow for flow in db.query(Flow).all()}
    sorted_flows = sorted(testcase.testcase_flows, key=lambda x: x.order_index)

    def _to_flow_detail(tf) -> TestcaseFlowDetailSchema:
        flow = flow_map.get(tf.flow_id)
        return TestcaseFlowDetailSchema(
            order=tf.order_index,
            flow_id=tf.flow_id,
            flow_name=flow.name if flow else "",
            enabled=tf.enabled,
            params=tf.params,
            requires=flow.requires or [] if flow else [],
        )

    # Get testcase_items with details
    item_repo = TestcaseItemRepository(db)
    testcase_items_dict = item_repo.get_items_with_details(testcase.id)

    return TestcaseDetailResponse(
        **build_testcase_response(testcase).model_dump(),
        setup_flows=[_to_flow_detail(tf) for tf in sorted_flows if tf.flow_role == "setup"],
        main_flows=[_to_flow_detail(tf) for tf in sorted_flows if tf.flow_role == "main"],
        teardown_flows=[_to_flow_detail(tf) for tf in sorted_flows if tf.flow_role == "teardown"],
        inline_steps=[
            InlineStepSchema(step_id=is_.step_id, order=is_.order_index, override_value=is_.override_value)
            for is_ in sorted(testcase.inline_steps, key=lambda x: x.order_index)
        ],
        testcase_items=[TestcaseItemResponseSchema(**item) for item in testcase_items_dict],
    )


def build_dependency_chain(db: Session, testcase) -> DependencyChainResponse:
    from app.models.screen import Screen
    from app.models.step import Step

    response_data = DependencyChainResponse(
        testcase_id=testcase.id,
        testcase_name=testcase.name,
        setup_flows=[],
        main_flows=[],
        teardown_flows=[],
        all_steps=[],
        required_profiles=[],
    )

    for tf in testcase.testcase_flows:
        flow = db.query(Flow).get(tf.flow_id)
        if not flow:
            continue
        flow_steps = []
        for fs in sorted(flow.flow_steps, key=lambda x: x.order_index):
            step = db.query(Step).get(fs.step_id)
            if not step:
                continue
            screen = db.query(Screen).get(step.screen_id)
            step_schema = DependencyChainStepSchema(
                order=fs.order_index,
                step_id=step.id,
                step_name=step.name,
                action_type=step.action_type,
                screen_name=screen.name if screen else None,
                element_name=step.element.name if step.element else None,
            )
            flow_steps.append(step_schema)
            response_data.all_steps.append(step_schema)

        flow_data = DependencyChainFlowSchema(
            flow_id=flow.id,
            flow_name=flow.name,
            steps=flow_steps,
            requires=flow.requires or [],
        )
        if tf.flow_role == "setup":
            response_data.setup_flows.append(flow_data)
        elif tf.flow_role == "main":
            response_data.main_flows.append(flow_data)
        elif tf.flow_role == "teardown":
            response_data.teardown_flows.append(flow_data)

    return response_data
