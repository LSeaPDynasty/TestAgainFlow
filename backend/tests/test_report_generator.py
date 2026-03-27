"""Tests for HTML report generator."""
from __future__ import annotations

from app.services.report_generator import ReportGenerator


def test_generate_html_report_basic():
    generator = ReportGenerator()
    html = generator.generate_html_report(
        task_id="task_1",
        task_info={"target_name": "DemoCase", "type": "testcase", "started_at": "2026-01-01"},
        logs=[{"timestamp": "t1", "level": "INFO", "message": "hello"}],
        screenshots=[{"filepath": "/tmp/a.png", "step_name": "step1", "timestamp": "t2"}],
        statistics={"total": 1, "success": 1, "failed": 0, "skipped": 0},
    )
    assert "Test Report" in html
    assert "task_1" in html
    assert "DemoCase" in html
    assert "hello" in html
    assert "/tmp/a.png" in html


def test_generate_html_report_with_embedded_images_uses_data_uri():
    generator = ReportGenerator()
    html = generator.generate_html_report_with_embedded_images(
        task_id="task_2",
        task_info={"target_name": "DemoSuite"},
        logs=[],
        screenshots=[{"base64": "ZmFrZQ==", "step_name": "failed-step"}],
        statistics={},
    )
    assert "data:image/png;base64,ZmFrZQ==" in html
