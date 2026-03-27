"""Service helpers for device endpoints."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.repositories.device_repo import DeviceRepository
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
from app.utils.adb import check_device_online, get_adb_devices
from app.utils.exceptions import NotFoundError

logger = logging.getLogger(__name__)


@dataclass
class ServiceValidationError:
    code: int
    message: str
    data: Optional[dict] = None


def list_devices(db: Session) -> dict:
    repo = DeviceRepository(db)
    devices = repo.list_all()

    try:
        adb_devices = get_adb_devices()
        adb_serials = {d["serial"] for d in adb_devices}
    except Exception:
        adb_devices = []
        adb_serials = set()

    results: List[Dict[str, Any]] = []
    serials_seen = set()
    for device in devices:
        serials_seen.add(device.serial)
        is_online = device.serial in adb_serials
        if is_online:
            try:
                is_online = check_device_online(device.serial)
            except Exception:
                is_online = False

        results.append(
            {
                "id": device.id,
                "name": device.name,
                "serial": device.serial,
                "model": device.model,
                "os_version": device.os_version,
                "connection_type": device.connection_type,
                "ip_port": device.ip_port,
                "capabilities": device.capabilities,
                "status": "online" if is_online else "offline",
            }
        )

    for adb_dev in adb_devices:
        if adb_dev["serial"] in serials_seen:
            continue
        results.append(
            {
                "id": None,
                "name": None,
                "serial": adb_dev["serial"],
                "model": None,
                "os_version": None,
                "connection_type": None,
                "ip_port": None,
                "capabilities": None,
                "status": "online",
                "_unconfigured": True,
            }
        )

    return {"total": len(results), "items": results}


def create_device(db: Session, device_in: DeviceCreate) -> tuple[Optional[DeviceResponse], Optional[ServiceValidationError]]:
    repo = DeviceRepository(db)
    if repo.get_by_serial(device_in.serial):
        return None, ServiceValidationError(code=4009, message="Device serial already exists")
    device = repo.create(device_in.model_dump())
    return _build_device_response(device), None


def update_device(
    db: Session,
    *,
    device_id: int,
    device_in: DeviceUpdate,
) -> DeviceResponse:
    repo = DeviceRepository(db)
    device = repo.get(device_id)
    if not device:
        raise NotFoundError(f"Device not found: id={device_id}")
    update_data = {k: v for k, v in device_in.model_dump().items() if v is not None}
    updated = repo.update(device_id, update_data)
    return _build_device_response(updated)


def delete_device(db: Session, device_id: int) -> None:
    repo = DeviceRepository(db)
    if not repo.delete(device_id):
        raise NotFoundError(f"Device not found: id={device_id}")


def register_engine_devices(db: Session, devices: List[dict]) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    device_repo = DeviceRepository(db)
    registered_devices = []

    try:
        for device_data in devices:
            serial = device_data.get("serial")
            if not serial:
                continue
            existing = device_repo.get_by_serial(serial)
            if existing:
                updated = device_repo.update(
                    existing.id,
                    {
                        "model": device_data.get("model"),
                        "os_version": device_data.get("os_version"),
                    },
                )
                registered_devices.append(
                    {"id": updated.id, "name": updated.name, "serial": updated.serial, "action": "updated"}
                )
            else:
                created = device_repo.create(
                    {
                        "name": device_data.get("name") or serial,
                        "serial": serial,
                        "model": device_data.get("model"),
                        "os_version": device_data.get("os_version"),
                        "connection_type": "usb",
                    }
                )
                registered_devices.append(
                    {"id": created.id, "name": created.name, "serial": created.serial, "action": "created"}
                )
        return {"message": f"Registered {len(registered_devices)} devices", "devices": registered_devices}, None
    except Exception as exc:
        logger.error("Device registration failed: %s", exc, exc_info=True)
        return None, ServiceValidationError(code=5000, message=f"Device registration failed: {exc}")


def handle_engine_disconnect(db: Session, executor_id: str, active_executors: dict) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    try:
        used_devices = []
        if executor_id in active_executors:
            tasks = active_executors[executor_id].get("tasks", [])
            for task in tasks:
                serial = task.get("device_serial")
                if serial:
                    used_devices.append(serial)

        repo = DeviceRepository(db)
        updated_count = 0
        for serial in used_devices:
            device = repo.get_by_serial(serial)
            if not device:
                continue
            repo.update(device.id, {})
            updated_count += 1
        return {"message": f"Marked {updated_count} devices as offline"}, None
    except Exception as exc:
        logger.error("Handle engine disconnect failed: %s", exc, exc_info=True)
        return None, ServiceValidationError(code=5000, message=f"Handle engine disconnect failed: {exc}")


def test_step_on_device(db: Session, device_id: int) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    try:
        repo = DeviceRepository(db)
        device = repo.get(device_id)
        if not device:
            return None, ServiceValidationError(code=4004, message="Device not found")
        return {
            "message": f"Device {device.name} step executed",
            "device_id": device_id,
            "serial": device.serial,
        }, None
    except Exception as exc:
        logger.error("Device step test failed: %s", exc, exc_info=True)
        return None, ServiceValidationError(code=5000, message=f"Device step test failed: {exc}")


async def test_device_connection(db: Session, serial: str) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    try:
        device_repo = DeviceRepository(db)
        device = device_repo.get_by_serial(serial)
        if not device:
            return None, ServiceValidationError(code=4004, message=f"Device not found: {serial}")

        from app.services.executor_bridge import ExecutorBridgeError, request_executor

        try:
            result = await request_executor(
                "test_device",
                {"serial": serial},
                request_prefix=f"test_device_{serial}",
                timeout_seconds=30.0,
                device_serial=serial,
            )
        except ExecutorBridgeError as exc:
            return None, ServiceValidationError(code=exc.http_code, message=exc.message)

        test_results = result.payload.get("results", {})
        return {
            "serial": serial,
            "online": test_results.get("connection") == "success",
            "message": test_results.get("message", "Device test completed"),
            "details": test_results,
            "executor_id": result.executor_id,
            "request_id": result.request_id,
        }, None
    except Exception as exc:
        logger.error("Device test failed: %s", exc, exc_info=True)
        return None, ServiceValidationError(code=5000, message=f"Device test failed: {exc}")


async def get_device_dom(db: Session, serial: str) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    """获取设备UI层次结构（DOM），通过WebSocket请求执行引擎"""
    try:
        device_repo = DeviceRepository(db)
        device = device_repo.get_by_serial(serial)
        if not device:
            return None, ServiceValidationError(code=4004, message=f"Device not found: {serial}")

        from app.services.executor_bridge import ExecutorBridgeError, request_executor

        try:
            result = await request_executor(
                "get_dom",
                {"serial": serial},
                request_prefix=f"get_dom_{serial}",
                timeout_seconds=30.0,
                device_serial=serial,
            )
        except ExecutorBridgeError as exc:
            return None, ServiceValidationError(code=exc.http_code, message=exc.message)

        return {
            "serial": serial,
            "dom_xml": result.payload.get("dom_xml", ""),
            "timestamp": result.payload.get("timestamp"),
        }, None
    except Exception as exc:
        logger.error("Get device DOM failed: %s", exc, exc_info=True)
        return None, ServiceValidationError(code=5000, message=f"Get device DOM failed: {exc}")


def _build_device_response(device: object) -> DeviceResponse:
    return DeviceResponse(
        id=device.id,
        name=device.name,
        serial=device.serial,
        model=device.model,
        os_version=device.os_version,
        connection_type=device.connection_type,
        ip_port=device.ip_port,
        capabilities=device.capabilities,
        adb_status="offline",
        created_at=device.created_at,
        updated_at=device.updated_at,
    )
