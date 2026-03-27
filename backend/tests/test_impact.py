"""Tests for impact endpoints."""
from __future__ import annotations


def test_analyze_element_impact(client, db, element, step):
    response = client.get(f"/api/v1/impact/elements/{element.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["element_id"] == element.id
    assert body["data"]["total_affected"] >= 1


def test_analyze_screen_impact(client, db, screen, element, step):
    response = client.get(f"/api/v1/impact/screens/{screen.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["screen_id"] == screen.id


def test_analyze_step_impact(client, db, step):
    response = client.get(f"/api/v1/impact/steps/{step.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["step_id"] == step.id


def test_analyze_flow_impact(client, db, flow, testcase):
    response = client.get(f"/api/v1/impact/flows/{flow.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["flow_id"] == flow.id


def test_health_check_start(client):
    response = client.post(
        "/api/v1/impact/health-check",
        json={"device_serial": "abc123def456", "screen_ids": []},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "running"
    assert body["data"]["task_id"].startswith("health_check_")
