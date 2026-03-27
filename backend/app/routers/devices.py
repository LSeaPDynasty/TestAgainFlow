"""Devices router."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.common import ApiResponse, ErrorCode
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
from app.services.device_service import (
    create_device as create_device_service,
    delete_device as delete_device_service,
    get_device_dom as get_device_dom_service,
    handle_engine_disconnect as handle_engine_disconnect_service,
    list_devices as list_devices_service,
    register_engine_devices as register_engine_devices_service,
    test_device_connection as test_device_connection_service,
    test_step_on_device as test_step_on_device_service,
    update_device as update_device_service,
)
from app.utils.response import error, ok

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("")
def list_devices(page: int = 1, page_size: int = 20, db: Session = Depends(get_db_session)):
    del page, page_size
    return ok(data=list_devices_service(db))


@router.post("", response_model=ApiResponse[DeviceResponse])
def create_device(device_in: DeviceCreate, db: Session = Depends(get_db_session)):
    response, validation_error = create_device_service(db, device_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Device created successfully")


@router.put("/{device_id}", response_model=ApiResponse[DeviceResponse])
def update_device(device_id: int, device_in: DeviceUpdate, db: Session = Depends(get_db_session)):
    return ok(data=update_device_service(db, device_id=device_id, device_in=device_in), message="Device updated successfully")


@router.delete("/{device_id}", response_model=ApiResponse)
def delete_device(device_id: int, db: Session = Depends(get_db_session)):
    delete_device_service(db, device_id)
    return ok(message="Device deleted successfully")


@router.post("/refresh-adb", response_model=ApiResponse[dict])
def refresh_adb(db: Session = Depends(get_db_session)):
    return list_devices(db=db)


@router.post("/refresh", response_model=ApiResponse[dict])
def refresh(db: Session = Depends(get_db_session)):
    return list_devices(db=db)


@router.post("/register")
async def register_engine_devices(devices: List[dict], db: Session = Depends(get_db_session)):
    response, validation_error = register_engine_devices_service(db, devices)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response)


@router.post("/engine-disconnect")
async def handle_engine_disconnect(executor_id: str, db: Session = Depends(get_db_session)):
    from app.routers import executor_status

    response, validation_error = handle_engine_disconnect_service(
        db,
        executor_id=executor_id,
        active_executors=executor_status.active_executors,
    )
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response)


@router.post("/{device_id}/test-step")
async def test_step_on_device(device_id: int, step_data: dict, db: Session = Depends(get_db_session)):
    del step_data
    response, validation_error = test_step_on_device_service(db, device_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response)


@router.post("/{serial}/test")
async def test_device_connection(serial: str, db: Session = Depends(get_db_session)):
    response, validation_error = await test_device_connection_service(db, serial)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response)


@router.get("/{serial}/dom")
async def get_device_dom(serial: str, db: Session = Depends(get_db_session)):
    """获取设备UI层次结构（DOM）"""
    response, validation_error = await get_device_dom_service(db, serial)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response)
