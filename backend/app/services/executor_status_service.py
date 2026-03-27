"""Service helpers for executor status."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.repositories.device_repo import DeviceRepository

active_executors: Dict[str, Dict[str, Any]] = {}


def get_executor_status() -> Dict[str, Any]:
    if not active_executors:
        return {"connected": False, "active_executors": 0, "executors": []}

    executors = []
    for executor_id, info in active_executors.items():
        executors.append(
            {
                "id": executor_id,
                "status": info.get("status", "unknown"),
                "connected_at": info.get("connected_at"),
                "last_heartbeat": info.get("last_heartbeat"),
                "active_tasks": info.get("active_tasks", 0),
                "queue_size": info.get("queue_size", 0),
            }
        )
    return {"connected": True, "active_executors": len(active_executors), "executors": executors}


def get_active_tasks() -> Dict[str, Any]:
    tasks = []
    for executor_id, info in active_executors.items():
        for task in info.get("tasks", []):
            tasks.append(
                {
                    "task_id": task.get("task_id"),
                    "executor_id": executor_id,
                    "status": task.get("status"),
                    "run_type": task.get("run_type"),
                    "target_id": task.get("target_id"),
                    "device_serial": task.get("device_serial"),
                    "started_at": task.get("started_at"),
                }
            )
    return {"total": len(tasks), "tasks": tasks}


def get_executor_devices(db: Session) -> Dict[str, Any]:
    used_devices = {}
    for executor_id, info in active_executors.items():
        for task in info.get("tasks", []):
            device_serial = task.get("device_serial")
            if device_serial:
                used_devices[device_serial] = {
                    "serial": device_serial,
                    "status": "in_use",
                    "in_use": True,
                    "current_executor": executor_id,
                    "current_task": task.get("task_id"),
                }

    device_repo = DeviceRepository(db)
    all_devices = device_repo.list()
    devices = []
    seen_serials = set()

    for serial, info in used_devices.items():
        seen_serials.add(serial)
        device = next((d for d in all_devices if d.serial == serial), None)
        if device:
            devices.append(
                {
                    "id": device.id,
                    "name": device.name,
                    "serial": device.serial,
                    "model": getattr(device, "model", "Unknown"),
                    "os_version": getattr(device, "os_version", "Unknown"),
                    "connection_type": device.connection_type,
                    "in_use": True,
                    "current_executor": info["current_executor"],
                    "current_task": info["current_task"],
                }
            )
        else:
            devices.append(
                {
                    "id": 0,
                    "name": serial,
                    "serial": serial,
                    "model": "Unknown",
                    "os_version": "Unknown",
                    "connection_type": "unknown",
                    "in_use": True,
                    "current_executor": info["current_executor"],
                    "current_task": info["current_task"],
                }
            )

    for device in all_devices:
        if device.serial not in seen_serials:
            devices.append(
                {
                    "id": device.id,
                    "name": device.name,
                    "serial": device.serial,
                    "model": getattr(device, "model", "Unknown"),
                    "os_version": getattr(device, "os_version", "Unknown"),
                    "connection_type": device.connection_type,
                    "in_use": False,
                    "current_executor": None,
                    "current_task": None,
                }
            )

    return {"total": len(devices), "devices": devices, "in_use_count": len(used_devices)}


def register_executor(executor_id: str, connection_info: Dict[str, Any]):
    active_executors[executor_id] = {
        "status": "connected",
        "connected_at": connection_info.get("connected_at"),
        "last_heartbeat": connection_info.get("connected_at"),
        "active_tasks": 0,
        "queue_size": 0,
        "tasks": [],
    }


def unregister_executor(executor_id: str):
    if executor_id in active_executors:
        del active_executors[executor_id]


def update_executor_heartbeat(executor_id: str):
    if executor_id in active_executors:
        active_executors[executor_id]["last_heartbeat"] = datetime.now().isoformat()


def update_executor_status(executor_id: str, status_data: Dict[str, Any]):
    if executor_id not in active_executors:
        register_executor(executor_id, status_data)

    active_executors[executor_id].update(
        {
            "status": status_data.get("status", "unknown"),
            "active_tasks": status_data.get("active_tasks", 0),
            "queue_size": status_data.get("queue_size", 0),
            "last_heartbeat": status_data.get("updated_at"),
        }
    )


def update_executor_task(executor_id: str, task_data: Dict[str, Any]):
    if executor_id not in active_executors:
        active_executors[executor_id] = {"tasks": [], "status": "connected"}

    tasks = active_executors[executor_id]["tasks"]
    task_id = task_data.get("task_id")
    updated = False
    for index, task in enumerate(tasks):
        if task.get("task_id") == task_id:
            tasks[index] = task_data
            updated = True
            break

    if not updated:
        tasks.append(task_data)

    current_active = [t for t in tasks if t.get("status") in ["running", "pending"]]
    active_executors[executor_id]["tasks"] = current_active
    active_executors[executor_id]["active_tasks"] = len(current_active)
