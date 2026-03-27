"""Service helpers for suites endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.suite_repo import SuiteRepository
from app.repositories.testcase_repo import TestcaseRepository
from app.schemas.suite import (
    SuiteCreate,
    SuiteDetailResponse,
    SuiteResponse,
    SuiteTestcaseSchema,
    SuiteToggleRequest,
    SuiteUpdate,
)


@dataclass
class ServiceValidationError:
    code: int
    message: str
    data: Optional[dict] = None


def list_suites(db: Session, *, skip: int, limit: int, project_id: Optional[int]):
    repo = SuiteRepository(db)
    return repo.list_with_testcase_count(skip=skip, limit=limit, project_id=project_id)


def get_suite_detail(db: Session, suite_id: int) -> Optional[SuiteDetailResponse]:
    repo = SuiteRepository(db)
    suite = repo.get_with_testcases(suite_id)
    if not suite:
        return None

    testcases_data = [
        SuiteTestcaseSchema(
            testcase_id=st.testcase_id,
            testcase_name=st.testcase.name if st.testcase else None,
            order=st.order_index,
            enabled=st.enabled,
        )
        for st in suite.suite_testcases
    ]
    return SuiteDetailResponse(
        id=suite.id,
        name=suite.name,
        description=suite.description,
        priority=suite.priority,
        enabled=suite.enabled,
        testcase_count=len(suite.suite_testcases),
        testcases=testcases_data,
        created_at=suite.created_at,
        updated_at=suite.updated_at,
    )


def create_suite(db: Session, suite_in: SuiteCreate) -> tuple[Optional[SuiteResponse], Optional[ServiceValidationError]]:
    repo = SuiteRepository(db)
    tc_repo = TestcaseRepository(db)

    if repo.get_by_name(suite_in.name):
        return None, ServiceValidationError(code=4009, message="Suite name already exists")

    if suite_in.testcases:
        for tc_data in suite_in.testcases:
            if not tc_repo.get(tc_data.testcase_id):
                return None, ServiceValidationError(
                    code=4004,
                    message=f"Testcase not found: id={tc_data.testcase_id}",
                )

    suite_data = suite_in.model_dump(exclude={"testcases"})
    suite = repo.create_with_testcases(
        {
            **suite_data,
            "testcases": [tc.model_dump() for tc in suite_in.testcases] if suite_in.testcases else None,
        }
    )
    return build_suite_response(suite), None


def update_suite(
    db: Session,
    *,
    suite_id: int,
    suite_in: SuiteUpdate,
) -> tuple[Optional[SuiteResponse], Optional[ServiceValidationError]]:
    repo = SuiteRepository(db)
    suite = repo.get(suite_id)
    if not suite:
        return None, ServiceValidationError(code=4004, message=f"Suite not found: id={suite_id}")

    if suite_in.name and suite_in.name != suite.name and repo.get_by_name(suite_in.name):
        return None, ServiceValidationError(code=4009, message="Suite name already exists")

    update_data = {
        k: v
        for k, v in suite_in.model_dump().items()
        if v is not None and k != "testcases"
    }
    updated = repo.update_with_testcases(
        suite_id,
        {
            **update_data,
            "testcases": [tc.model_dump() for tc in suite_in.testcases] if suite_in.testcases else None,
        },
    )
    return build_suite_response(updated), None


def delete_suite(db: Session, suite_id: int) -> Optional[ServiceValidationError]:
    repo = SuiteRepository(db)
    if not repo.delete(suite_id):
        return ServiceValidationError(code=4004, message=f"Suite not found: id={suite_id}")
    return None


def toggle_suite(
    db: Session,
    *,
    suite_id: int,
    req: SuiteToggleRequest,
) -> tuple[Optional[SuiteResponse], Optional[ServiceValidationError]]:
    repo = SuiteRepository(db)
    suite = repo.toggle_enabled(suite_id, req.enabled)
    if not suite:
        return None, ServiceValidationError(code=4004, message=f"Suite not found: id={suite_id}")
    return build_suite_response(suite), None


def build_suite_response(suite: object) -> SuiteResponse:
    return SuiteResponse(
        id=suite.id,
        name=suite.name,
        description=suite.description,
        priority=suite.priority,
        enabled=suite.enabled,
        testcase_count=len(suite.suite_testcases) if suite.suite_testcases else 0,
        created_at=suite.created_at,
        updated_at=suite.updated_at,
    )
