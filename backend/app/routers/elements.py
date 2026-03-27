"""Elements router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.element import ElementCreate, ElementResponse, ElementTestRequest, ElementUpdate
from app.services.element_service import (
    create_element as create_element_service,
    delete_element as delete_element_service,
    get_element as get_element_service,
    list_elements as list_elements_service,
    test_element_locator as test_element_locator_service,
    update_element as update_element_service,
)
from app.utils.pagination import calculate_offset
from app.utils.response import error, ok

router = APIRouter(prefix="/elements", tags=["elements"])


@router.get("", response_model=ApiResponse[PaginatedResponse[ElementResponse]])
def list_elements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    search: str = Query(None),
    screen_id: int = Query(None),
    locator_type: str = Query(None),
    db: Session = Depends(get_db_session),
):
    results, total = list_elements_service(
        db,
        skip=calculate_offset(page, page_size),
        limit=page_size,
        search=search,
        screen_id=screen_id,
        locator_type=locator_type,
    )
    return ok(data=PaginatedResponse(items=results, total=total, page=page, page_size=page_size))


@router.get("/{element_id}", response_model=ApiResponse[ElementResponse])
def get_element(element_id: int, db: Session = Depends(get_db_session)):
    response, validation_error = get_element_service(db, element_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response)


@router.post("", response_model=ApiResponse[ElementResponse])
def create_element(element_in: ElementCreate, db: Session = Depends(get_db_session)):
    response, validation_error = create_element_service(db, element_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Element created successfully")


@router.put("/{element_id}", response_model=ApiResponse[ElementResponse])
def update_element(element_id: int, element_in: ElementUpdate, db: Session = Depends(get_db_session)):
    response, validation_error = update_element_service(db, element_id=element_id, element_in=element_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Element updated successfully")


@router.delete("/{element_id}", response_model=ApiResponse)
def delete_element(element_id: int, db: Session = Depends(get_db_session)):
    validation_error = delete_element_service(db, element_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(message="Element deleted successfully")


@router.post("/{element_id}/test")
async def test_element_locator(element_id: int, test_req: ElementTestRequest, db: Session = Depends(get_db_session)):
    response, validation_error = await test_element_locator_service(
        db,
        element_id=element_id,
        device_serial=test_req.device_serial,
        locator_index=test_req.locator_index,
    )
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response)
