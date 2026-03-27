"""Testcases router."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.testcase import (
    DependencyChainResponse,
    TestcaseCreate,
    TestcaseDetailResponse,
    TestcaseDuplicateRequest,
    TestcaseItemUpdateSchema,
    TestcaseResponse,
    TestcaseUpdate,
)
from app.services.testcase_service import (
    create_testcase as create_testcase_service,
    delete_testcase as delete_testcase_service,
    duplicate_testcase as duplicate_testcase_service,
    get_dependency_chain_for_testcase,
    get_testcase_detail,
    list_testcases as list_testcases_service,
    update_testcase as update_testcase_service,
)
from app.utils.pagination import calculate_offset
from app.utils.response import error, ok

router = APIRouter(prefix="/testcases", tags=["testcases"])


@router.get("", response_model=ApiResponse[PaginatedResponse[TestcaseResponse]])
def list_testcases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    search: str = Query(None),
    priority: str = Query(None),
    tag_id: int = Query(None),
    tag_ids: str = Query(None),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db_session),
):
    results, total = list_testcases_service(
        db,
        skip=calculate_offset(page, page_size),
        limit=page_size,
        search=search,
        priority=priority,
        tag_id=tag_id,
        tag_ids=tag_ids,
        project_id=project_id,
    )
    return ok(data=PaginatedResponse(items=results, total=total, page=page, page_size=page_size))


@router.get("/{testcase_id}", response_model=ApiResponse[TestcaseDetailResponse])
def get_testcase(testcase_id: int, db: Session = Depends(get_db_session)):
    response = get_testcase_detail(db, testcase_id)
    if not response:
        return error(code=4004, message="Testcase not found")
    return ok(data=response)


@router.post("", response_model=ApiResponse[TestcaseResponse])
def create_testcase(testcase_in: TestcaseCreate, db: Session = Depends(get_db_session)):
    response, validation_error = create_testcase_service(db, testcase_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message)
    return ok(data=response, message="Testcase created successfully")


@router.put("/{testcase_id}", response_model=ApiResponse[TestcaseResponse])
def update_testcase(testcase_id: int, testcase_in: TestcaseUpdate, db: Session = Depends(get_db_session)):
    response, validation_error = update_testcase_service(db, testcase_id, testcase_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message)
    return ok(data=response, message="Testcase updated successfully")


@router.delete("/{testcase_id}", response_model=ApiResponse)
def delete_testcase(testcase_id: int, db: Session = Depends(get_db_session)):
    validation_error, err_data = delete_testcase_service(db, testcase_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=err_data)
    return ok(message="Testcase deleted successfully")


@router.post("/{testcase_id}/duplicate", response_model=ApiResponse[TestcaseResponse])
def duplicate_testcase(testcase_id: int, req: TestcaseDuplicateRequest, db: Session = Depends(get_db_session)):
    response, validation_error = duplicate_testcase_service(db, testcase_id, req.new_name)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message)
    return ok(data=response, message="Testcase duplicated successfully")


@router.get("/{testcase_id}/dependency-chain", response_model=ApiResponse[DependencyChainResponse])
def get_dependency_chain(testcase_id: int, db: Session = Depends(get_db_session)):
    response, validation_error = get_dependency_chain_for_testcase(db, testcase_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message)
    return ok(data=response)


@router.post("/batch", response_model=ApiResponse)
async def batch_create_testcases(
    request: dict,
    db: Session = Depends(get_db_session),
):
    """Batch create testcases with recursive dependency creation."""
    try:
        from app.services.batch_import_service import BatchImportService

        # Supports:
        # 1) {"project_id": 1, "testcases": [{...}, {...}]}
        # 2) single testcase payload directly: {"name": "...", "main_flows": [...]}
        if isinstance(request.get("testcases"), list):
            testcases = request.get("testcases", [])
        else:
            testcases = [request]

        project_id = request.get("project_id")
        if not testcases:
            return error(code=4001, message="Request must contain at least one testcase")

        service = BatchImportService(db)

        created_count = 0
        failed_cases = []
        import_details = {
            "created": {"screens": [], "elements": [], "steps": [], "flows": [], "testcases": []},
            "reused": {"screens": [], "elements": [], "steps": [], "flows": [], "testcases": []},
        }

        for tc_data in testcases:
            try:
                result = await service.import_testcase_with_dependencies(
                    testcase_data=tc_data,
                    project_id=project_id,
                )

                if result.get("success"):
                    created_count += 1
                    for key in import_details["created"]:
                        import_details["created"][key].extend(result["created"].get(key, []))
                    for key in import_details["reused"]:
                        import_details["reused"][key].extend(result["reused"].get(key, []))
                else:
                    failed_cases.append(
                        {
                            "name": tc_data.get("case_name", tc_data.get("name", "unknown")),
                            "error": "; ".join(result.get("errors", ["unknown error"])),
                        }
                    )
            except Exception as exc:
                failed_cases.append(
                    {
                        "name": tc_data.get("case_name", tc_data.get("name", "unknown")),
                        "error": str(exc),
                    }
                )

        for bucket in ("created", "reused"):
            for key, values in import_details[bucket].items():
                import_details[bucket][key] = list(dict.fromkeys(values))

        return ok(
            data={
                "count": created_count,
                "failed": failed_cases,
                "details": import_details,
            },
            message=f"Batch import finished: success {created_count}, failed {len(failed_cases)}",
        )
    except Exception as exc:
        return error(code=5000, message=f"Batch import failed: {str(exc)}")


@router.put("/{testcase_id}/items", response_model=ApiResponse)
def update_testcase_items(
    testcase_id: int,
    request: TestcaseItemUpdateSchema,
    db: Session = Depends(get_db_session),
):
    """
    Update testcase items (full replacement)

    This endpoint replaces all existing testcase_items with the provided list.
    Use this for drag-and-drop reordering and bulk updates.

    Request body example:
    {
        "items": [
            {"item_type": "flow", "flow_id": 101, "order_index": 1, "enabled": true},
            {"item_type": "step", "step_id": 5001, "order_index": 2, "enabled": true, "continue_on_error": false},
            {"item_type": "step", "step_id": 5002, "order_index": 3, "enabled": true}
        ]
    }
    """
    from app.models.testcase_item import TestcaseItem
    from app.models.testcase import Testcase
    from sqlalchemy import select, delete

    # Verify testcase exists
    testcase = db.query(Testcase).filter_by(id=testcase_id).first()
    if not testcase:
        return error(code=4004, message="Testcase not found")

    try:
        # Delete all existing items for this testcase
        db.execute(delete(TestcaseItem).where(TestcaseItem.testcase_id == testcase_id))

        # Insert new items
        for item_data in request.items:
            # Validate consistency
            if item_data.item_type == 'flow' and not item_data.flow_id:
                return error(code=4000, message=f"flow_id is required when item_type is 'flow'")
            if item_data.item_type == 'step' and not item_data.step_id:
                return error(code=4000, message=f"step_id is required when item_type is 'step'")

            item = TestcaseItem(
                testcase_id=testcase_id,
                item_type=item_data.item_type,
                flow_id=item_data.flow_id,
                step_id=item_data.step_id,
                order_index=item_data.order_index,
                enabled=item_data.enabled,
                continue_on_error=item_data.continue_on_error,
                params=item_data.params
            )
            db.add(item)

        db.commit()

        return ok(data={
            "testcase_id": testcase_id,
            "items_count": len(request.items),
            "message": f"Successfully updated {len(request.items)} items"
        }, message="Testcase items updated successfully")

    except Exception as exc:
        db.rollback()
        return error(code=5000, message=f"Failed to update testcase items: {str(exc)}")


@router.get("/{testcase_id}/items", response_model=ApiResponse)
def get_testcase_items(
    testcase_id: int,
    db: Session = Depends(get_db_session),
):
    """
    Get testcase items with expanded flow/step information

    Returns the unified execution sequence with flow/step names and action types.
    """
    from app.models.testcase_item import TestcaseItem
    from sqlalchemy import select

    # Verify testcase exists
    testcase = db.query(Testcase).filter_by(id=testcase_id).first()
    if not testcase:
        return error(code=4004, message="Testcase not found")

    try:
        # Query items with expanded info
        query = (
            select(
                TestcaseItem.id,
                TestcaseItem.testcase_id,
                TestcaseItem.item_type,
                TestcaseItem.flow_id,
                TestcaseItem.step_id,
                TestcaseItem.order_index,
                TestcaseItem.enabled,
                TestcaseItem.continue_on_error,
                TestcaseItem.params,
                # Expanded fields
                TestcaseItem.created_at,
                TestcaseItem.updated_at
            )
            .where(TestcaseItem.testcase_id == testcase_id)
            .order_by(TestcaseItem.order_index)
        )

        items = db.execute(query).all()

        # Expand with flow/step names
        result_items = []
        for item in items:
            item_dict = {
                "id": item.id,
                "testcase_id": item.testcase_id,
                "item_type": item.item_type,
                "flow_id": item.flow_id,
                "step_id": item.step_id,
                "order_index": item.order_index,
                "enabled": item.enabled,
                "continue_on_error": item.continue_on_error,
                "params": item.params,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }

            # Expand flow info
            if item.item_type == 'flow' and item.flow_id:
                from app.models.flow import Flow
                flow = db.query(Flow).filter_by(id=item.flow_id).first()
                item_dict["flow_name"] = flow.name if flow else None

            # Expand step info
            if item.item_type == 'step' and item.step_id:
                from app.models.step import Step
                step = db.query(Step).filter_by(id=item.step_id).first()
                item_dict["step_name"] = step.name if step else None
                item_dict["step_action_type"] = step.action_type if step else None

            result_items.append(item_dict)

        return ok(data={
            "testcase_id": testcase_id,
            "items": result_items,
            "total": len(result_items)
        })

    except Exception as exc:
        return error(code=5000, message=f"Failed to get testcase items: {str(exc)}")
