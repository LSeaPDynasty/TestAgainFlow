"""Tests for task queue requeue/cleanup behavior."""
from __future__ import annotations

import pytest

from app.utils.task_queue import TaskQueue


@pytest.mark.asyncio
async def test_requeue_non_final_task():
    queue = TaskQueue()
    queue.put_nowait("task_1", {"name": "demo"})

    first = await queue.get(timeout=0.1)
    assert first == "task_1"
    assert queue.get_status("task_1") == "picked_up"

    requeued = queue.requeue("task_1")
    assert requeued is True
    assert queue.get_status("task_1") == "queued"

    second = await queue.get(timeout=0.1)
    assert second == "task_1"


def test_requeue_final_task_returns_false():
    queue = TaskQueue()
    queue.put_nowait("task_2", {"name": "done"})
    queue.update_task_status("task_2", "completed")

    assert queue.requeue("task_2") is False


def test_clear_removes_task_metadata():
    queue = TaskQueue()
    queue.put_nowait("task_3", {"name": "cleanup"})
    assert queue.get_task_data("task_3") is not None
    assert queue.get_status("task_3") == "queued"

    queue.clear()

    assert queue.get_queue_size() == 0
    assert queue.get_task_data("task_3") is None
    assert queue.get_status("task_3") is None
