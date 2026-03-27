"""
Context Builder - build execution context for test runs
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.testcase import Testcase, TestcaseFlow
from app.models.flow import Flow, FlowStep
from app.models.step import Step
from app.models.profile import Profile
from app.models.data_store import DataStore


def build_execution_context(
    db: Session,
    testcase: Testcase,
    profile_id: Optional[int],
    device_serial: Optional[str]
) -> Dict[str, Any]:
    """
    Build complete execution context for a testcase

    Returns context dict with:
    - testcase: testcase info
    - variables: merged variables (testcase params > profile > data_store)
    - flows: expanded flow list with steps
    - device: device info
    """
    # Build variable hierarchy
    variables = {}

    # 1. DataStore variables (lowest priority)
    data_store_records = db.query(DataStore).all()
    for record in data_store_records:
        variables[record.key_name] = record.value

    # 2. Profile variables (medium priority)
    if profile_id:
        profile = db.get(Profile, profile_id)
        if profile and profile.variables:
            variables.update(profile.variables)

    # 3. Testcase params (highest priority)
    if testcase.params:
        variables.update(testcase.params)

    # Build flows with steps
    flows = []

    # Add setup flows
    setup_flows = db.query(TestcaseFlow).filter(
        TestcaseFlow.testcase_id == testcase.id,
        TestcaseFlow.flow_role == 'setup',
        TestcaseFlow.enabled == True
    ).order_by(TestcaseFlow.order_index).all()

    for tf in setup_flows:
        flow_data = _build_flow_data(db, tf, variables)
        flow_data['role'] = 'setup'
        flows.append(flow_data)

    # Add main flows
    main_flows = db.query(TestcaseFlow).filter(
        TestcaseFlow.testcase_id == testcase.id,
        TestcaseFlow.flow_role == 'main',
        TestcaseFlow.enabled == True
    ).order_by(TestcaseFlow.order_index).all()

    for tf in main_flows:
        flow_data = _build_flow_data(db, tf, variables)
        flow_data['role'] = 'main'
        flows.append(flow_data)

    # Add teardown flows
    teardown_flows = db.query(TestcaseFlow).filter(
        TestcaseFlow.testcase_id == testcase.id,
        TestcaseFlow.flow_role == 'teardown',
        TestcaseFlow.enabled == True
    ).order_by(TestcaseFlow.order_index).all()

    for tf in teardown_flows:
        flow_data = _build_flow_data(db, tf, variables)
        flow_data['role'] = 'teardown'
        flows.append(flow_data)

    # Build context
    context = {
        'testcase': {
            'id': testcase.id,
            'name': testcase.name,
            'priority': testcase.priority,
            'timeout': testcase.timeout
        },
        'variables': variables,
        'flows': flows,
        'device': {
            'serial': device_serial
        } if device_serial else None
    }

    return context


def _build_flow_data(
    db: Session,
    testcase_flow: TestcaseFlow,
    variables: Dict[str, str]
) -> Dict[str, Any]:
    """Build flow data with steps"""
    flow = db.get(Flow, testcase_flow.flow_id)
    if not flow:
        return None

    # Merge flow params with testcase flow params
    flow_params = testcase_flow.params or {}

    # Build steps list
    steps = []

    if flow.flow_type == 'standard':
        flow_steps = db.query(FlowStep).filter(
            FlowStep.flow_id == flow.id
        ).order_by(FlowStep.order_index).all()

        for fs in flow_steps:
            step = db.get(Step, fs.step_id)
            if step:
                step_data = {
                    'id': step.id,
                    'name': step.name,
                    'action_type': step.action_type,
                    'screen_id': step.screen_id,
                    'element_id': step.element_id,
                    'action_value': fs.override_value or step.action_value,
                    'assert_config': step.assert_config,
                    'wait_after_ms': step.wait_after_ms
                }
                steps.append(step_data)

    elif flow.flow_type == 'dsl' and flow.dsl_content:
        # Parse DSL and expand
        from app.utils.dsl_parser import DslParser
        from app.repositories.flow_repo import FlowRepository
        flow_repo = FlowRepository(db)
        expanded, _ = DslParser.parse(flow.dsl_content)

        for exp_step in expanded:
            if exp_step['type'] == 'step':
                step = db.get(Step, exp_step['step_id'])
                if step:
                    steps.append({
                        'id': step.id,
                        'name': step.name,
                        'action_type': step.action_type,
                        'screen_id': step.screen_id,
                        'element_id': step.element_id,
                        'action_value': step.action_value,
                        'assert_config': step.assert_config,
                        'wait_after_ms': step.wait_after_ms
                    })

    return {
        'id': flow.id,
        'name': flow.name,
        'flow_type': flow.flow_type,
        'params': flow_params,
        'steps': steps
    }
