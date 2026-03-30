"""Service helpers for flows router."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import yaml
from sqlalchemy.orm import Session, joinedload

from app.models.step import Step
from app.schemas.flow import (
    DslValidateResponse,
    ExpandedStepSchema,
    FlowCreate,
    FlowDetailResponse,
    FlowResponse,
    FlowStepDetailSchema,
    FlowUpdate,
    TagSchema,
)
from app.utils.dsl_parser import DslParser

VALID_FLOW_TYPES = {"standard", "dsl", "python"}


@dataclass
class ServiceValidationError:
    code: int
    message: str


def parse_tag_ids(tag_ids: Optional[str]) -> Optional[list[int]]:
    if not tag_ids:
        return None
    return [int(t) for t in tag_ids.split(",") if t.strip().isdigit()]


def validate_flow_create(flow_in: FlowCreate, repo, step_repo) -> Optional[ServiceValidationError]:
    if not flow_in.name or not flow_in.name.strip():
        return ServiceValidationError(code=4001, message="Flow name cannot be empty")
    if flow_in.flow_type not in VALID_FLOW_TYPES:
        return ServiceValidationError(
            code=4001,
            message=f"Invalid flow_type: {flow_in.flow_type}. Must be one of: standard, dsl, python",
        )
    if repo.get_by_name(flow_in.name):
        return ServiceValidationError(code=4009, message="Flow name already exists")
    if flow_in.flow_type == "standard" and not flow_in.steps:
        return ServiceValidationError(code=4001, message="standard type flow must have steps")
    if flow_in.flow_type == "dsl" and not flow_in.dsl_content:
        return ServiceValidationError(code=4001, message="dsl type flow must have dsl_content")

    if flow_in.flow_type == "dsl" and flow_in.dsl_content:
        parser = DslParser()
        _, errors = parser.parse(flow_in.dsl_content)
        if errors:
            error_msg = errors[0].get("message", "") if errors else ""
            if "yaml" in error_msg.lower() or "syntax" in error_msg.lower():
                return ServiceValidationError(
                    code=4001, message=f"Invalid YAML syntax: {error_msg}"
                )

    if flow_in.steps:
        for step in flow_in.steps:
            if not step_repo.get(step.step_id):
                return ServiceValidationError(
                    code=4004, message=f"Step not found: step_id={step.step_id}"
                )
    return None


def build_create_payload(flow_in: FlowCreate) -> dict:
    return flow_in.model_dump(exclude={"tag_ids"})


def build_update_payload(flow: object, flow_in: FlowUpdate) -> dict:
    update_data = {
        k: v
        for k, v in flow_in.model_dump().items()
        if v is not None and k not in ["tag_ids", "steps"]
    }
    if "flow_type" not in update_data:
        update_data["flow_type"] = flow.flow_type
    payload = {
        **update_data,
        "tag_ids": flow_in.tag_ids,
    }
    if flow_in.steps is not None:
        payload["steps"] = flow_in.steps
    return payload


def calculate_expanded_count(flow_type: str, dsl_content: Optional[str], step_count: int) -> int:
    if flow_type != "dsl" or not dsl_content:
        return step_count
    parser = DslParser()
    expanded_steps, _ = parser.parse(dsl_content)
    return len(expanded_steps)


def build_flow_response(flow: object, repo, *, expanded_step_count: Optional[int] = None) -> FlowResponse:
    step_count = len(flow.flow_steps)
    return FlowResponse(
        id=flow.id,
        name=flow.name,
        description=flow.description,
        flow_type=flow.flow_type,
        requires=flow.requires or [],
        default_params=flow.default_params,
        step_count=step_count,
        expanded_step_count=expanded_step_count if expanded_step_count is not None else step_count,
        tags=[TagSchema(id=t.id, name=t.name) for t in flow.tags],
        referenced_by_testcase_count=repo.check_testcase_usage(flow.id),
        created_at=flow.created_at,
        updated_at=flow.updated_at,
    )


def build_flow_detail_response(db: Session, flow: object, repo) -> FlowDetailResponse:
    steps_detail = []
    for fs in sorted(flow.flow_steps, key=lambda x: x.order_index):
        step = (
            db.query(Step)
            .options(joinedload(Step.screen), joinedload(Step.element))
            .filter(Step.id == fs.step_id)
            .first()
        )
        if step:
            # 获取元素描述
            element_description = None
            if step.element:
                element_description = step.element.description

            steps_detail.append(
                FlowStepDetailSchema(
                    order=fs.order_index,
                    step_id=fs.step_id,
                    step_name=step.name,
                    action_type=step.action_type,
                    screen_name=step.screen.name if step.screen else None,
                    element_name=step.element.name if step.element else None,
                    element_description=element_description,
                    override_value=fs.override_value,
                )
            )

    return FlowDetailResponse(
        **build_flow_response(flow, repo).model_dump(),
        dsl_content=flow.dsl_content,
        py_file=flow.py_file,
        steps=steps_detail,
        expanded_count=len(flow.flow_steps),
    )


def validate_dsl_content(db: Session, dsl_content: str) -> DslValidateResponse:
    normalized_content = dsl_content
    try:
        parsed_yaml = yaml.safe_load(dsl_content)
        if isinstance(parsed_yaml, list):
            normalized_steps = []
            for item in parsed_yaml:
                if not isinstance(item, dict):
                    normalized_steps.append(item)
                    continue
                normalized_item = dict(item)
                # Backward compatibility:
                # - flow_name: X
                # - flow_name: X + call: {params: ...}
                if "flow_name" in normalized_item:
                    normalized_item["call"] = normalized_item.get("flow_name")
                    normalized_item.pop("flow_name", None)
                normalized_steps.append(normalized_item)
            normalized_content = yaml.safe_dump(
                normalized_steps,
                allow_unicode=True,
                sort_keys=False,
            )
    except Exception:
        normalized_content = dsl_content

    parser = DslParser()
    expanded_steps, errors = parser.parse(normalized_content)

    from app.repositories.flow_repo import FlowRepository

    flow_repo = FlowRepository(db)
    errors.extend(parser.validate_step_references(expanded_steps, flow_repo))
    error_messages = [error.get("message", str(error)) for error in errors]

    return DslValidateResponse(
        valid=len(errors) == 0,
        errors=error_messages,
        expanded_steps=[ExpandedStepSchema(**step) for step in expanded_steps],
        expanded_count=len(expanded_steps),
    )
