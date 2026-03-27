"""
DSL Parser - parse and validate DSL content
"""
from typing import List, Dict, Any, Optional
import yaml
from app.utils.exceptions import ValidationError


class DslParser:
    """DSL parser for flow DSL content"""

    # Valid action types
    VALID_ACTIONS = {
        'click', 'long_press', 'input', 'swipe', 'hardware_back',
        'wait_element', 'wait_time',
        'assert_text', 'assert_exists', 'assert_not_exists', 'assert_color',
        'repeat', 'break_if', 'set', 'call',
        'start_activity', 'screenshot', 'py_step'
    }

    @staticmethod
    def parse(dsl_content: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parse DSL content and return expanded steps and errors

        Returns:
            (expanded_steps, errors)
        """
        if not dsl_content or not dsl_content.strip():
            return [], [{"line": 0, "message": "DSL content is empty"}]

        errors = []
        expanded_steps = []

        try:
            # Parse YAML
            steps_data = yaml.safe_load(dsl_content)
            if not isinstance(steps_data, list):
                errors.append({"line": 0, "message": "DSL must be a list of steps"})
                return [], errors

            # Expand steps
            order = 1
            for idx, step_data in enumerate(steps_data, start=1):
                step_errors, step_expanded = DslParser._expand_step(step_data, idx, order)
                errors.extend(step_errors)
                expanded_steps.extend(step_expanded)
                order = len(expanded_steps) + 1

        except yaml.YAMLError as e:
            errors.append({"line": 0, "message": f"YAML parsing error: {str(e)}"})
        except Exception as e:
            errors.append({"line": 0, "message": f"Unexpected error: {str(e)}"})

        return expanded_steps, errors

    @staticmethod
    def _expand_step(step_data: Any, line: int, start_order: int) -> tuple[List[Dict], List[Dict]]:
        """Expand a single step (handle repeat, call, etc.)"""
        errors = []
        expanded = []

        if not isinstance(step_data, dict):
            errors.append({"line": line, "message": "Step must be a dictionary"})
            return errors, expanded

        # Handle 'repeat' action
        if 'repeat' in step_data:
            return DslParser._expand_repeat(step_data, line, start_order)

        # Handle 'call' action
        if 'call' in step_data:
            flow_name = step_data['call']
            if not isinstance(flow_name, str):
                errors.append({"line": line, "message": "call value must be a string"})
            else:
                expanded.append({
                    'order': start_order,
                    'type': 'call',
                    'target': flow_name
                })
            return errors, expanded

        # Handle 'break_if' action
        if 'break_if' in step_data:
            condition = step_data['break_if']
            expanded.append({
                'order': start_order,
                'type': 'break_if',
                'condition': condition
            })
            return errors, expanded

        # Handle 'set' action
        if 'set' in step_data:
            var_data = step_data['set']
            if isinstance(var_data, dict):
                for var_name, var_value in var_data.items():
                    expanded.append({
                        'order': start_order,
                        'type': 'set',
                        'variable': var_name,
                        'value': var_value
                    })
                    start_order += 1
            return errors, expanded

        # Regular step with step_id
        if 'step_id' in step_data:
            step_id = step_data['step_id']
            if not isinstance(step_id, int):
                errors.append({"line": line, "message": "step_id must be an integer"})
            else:
                expanded.append({
                    'order': start_order,
                    'type': 'step',
                    'step_id': step_id
                })
        else:
            errors.append({"line": line, "message": "Step must have step_id, call, repeat, or break_if"})

        return errors, expanded

    @staticmethod
    def _expand_repeat(step_data: Dict, line: int, start_order: int) -> tuple[List[Dict], List[Dict]]:
        """Expand repeat action"""
        errors = []
        expanded = []

        repeat_value = step_data['repeat']
        do_steps = step_data.get('do', [])

        if not isinstance(repeat_value, int) or repeat_value < 1:
            errors.append({"line": line, "message": "repeat must be a positive integer"})
            return errors, expanded

        # If no 'do' field, repeat the current step itself
        if not do_steps:
            # Get the step_id from the current step
            step_id = step_data.get('step_id')
            if step_id:
                for i in range(repeat_value):
                    expanded.append({
                        'order': start_order + i,
                        'type': 'step',
                        'step_id': step_id
                    })
                return errors, expanded
            else:
                errors.append({"line": line, "message": "repeat without 'do' must have step_id"})
                return errors, expanded

        if not isinstance(do_steps, list):
            errors.append({"line": line, "message": "do must be a list of steps"})
            return errors, expanded

        # Expand repeat with 'do' steps
        for i in range(repeat_value):
            for idx, sub_step in enumerate(do_steps, start=1):
                sub_errors, sub_expanded = DslParser._expand_step(
                    sub_step, line + idx, start_order
                )
                errors.extend(sub_errors)
                expanded.extend(sub_expanded)
                start_order = len(expanded) + 1

        return errors, expanded

    @staticmethod
    def validate_step_references(expanded_steps: List[Dict], flow_repo) -> List[Dict]:
        """Validate that all referenced step_ids and flow_names exist"""
        errors = []

        for step in expanded_steps:
            if step['type'] == 'step':
                step_id = step.get('step_id')
                if step_id:
                    from app.models.step import Step
                    if not flow_repo.db.get(Step, step_id):
                        errors.append({"line": 0, "message": f"Step not found: step_id={step_id}"})

            elif step['type'] == 'call':
                flow_name = step.get('target')
                if flow_name:
                    from app.models.flow import Flow
                    existing_flow = flow_repo.db.query(Flow).filter(Flow.name == flow_name).first()
                    if not existing_flow:
                        errors.append({"line": 0, "message": f"Flow not found: {flow_name}"})

        return errors
