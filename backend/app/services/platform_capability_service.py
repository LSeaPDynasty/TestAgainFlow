"""Platform capability matrix and validation helpers."""
from __future__ import annotations

from typing import Iterable, Set

from sqlalchemy.orm import Session

from app.models.flow import FlowStep
from app.models.step import Step
from app.models.suite import SuiteTestcase
from app.models.testcase import TestcaseFlow, TestcaseInlineStep

ANDROID_SUPPORTED_ACTIONS: Set[str] = {
    "click",
    "long_press",
    "input",
    "swipe",
    "hardware_back",
    "wait_element",
    "wait_time",
    "assert_text",
    "assert_exists",
    "assert_not_exists",
    "assert_color",
    "start_activity",
    "screenshot",
}

# Placeholder sets. Concrete implementations can be expanded when drivers land.
IOS_SUPPORTED_ACTIONS: Set[str] = set()
WEB_SUPPORTED_ACTIONS: Set[str] = set()

PLATFORM_ACTION_MATRIX: dict[str, Set[str]] = {
    "android": ANDROID_SUPPORTED_ACTIONS,
    "ios": IOS_SUPPORTED_ACTIONS,
    "web": WEB_SUPPORTED_ACTIONS,
}


def normalize_platform(platform: str | None) -> str:
    return (platform or "android").strip().lower()


def get_platform_supported_actions(platform: str) -> Set[str] | None:
    return PLATFORM_ACTION_MATRIX.get(normalize_platform(platform))


def collect_actions_for_testcases(db: Session, testcase_ids: Iterable[int]) -> Set[str]:
    ids = {int(i) for i in testcase_ids if i is not None}
    if not ids:
        return set()

    flow_actions = (
        db.query(Step.action_type)
        .join(FlowStep, FlowStep.step_id == Step.id)
        .join(TestcaseFlow, TestcaseFlow.flow_id == FlowStep.flow_id)
        .filter(TestcaseFlow.testcase_id.in_(ids), TestcaseFlow.enabled == 1)
        .all()
    )
    inline_actions = (
        db.query(Step.action_type)
        .join(TestcaseInlineStep, TestcaseInlineStep.step_id == Step.id)
        .filter(TestcaseInlineStep.testcase_id.in_(ids))
        .all()
    )

    return {row[0] for row in (flow_actions + inline_actions) if row and row[0]}


def collect_actions_for_suites(db: Session, suite_ids: Iterable[int]) -> Set[str]:
    ids = {int(i) for i in suite_ids if i is not None}
    if not ids:
        return set()

    testcase_ids = {
        row[0]
        for row in db.query(SuiteTestcase.testcase_id)
        .filter(SuiteTestcase.suite_id.in_(ids), SuiteTestcase.enabled == 1)
        .all()
        if row and row[0]
    }
    return collect_actions_for_testcases(db, testcase_ids)
