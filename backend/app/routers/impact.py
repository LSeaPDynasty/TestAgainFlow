"""Impact router - impact analysis."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.common import ApiResponse
from app.schemas.impact import HealthCheckRequest, HealthCheckResponse, ImpactResponse
from app.services.impact_service import (
    analyze_element_impact as build_element_impact,
    analyze_flow_impact as build_flow_impact,
    analyze_screen_impact as build_screen_impact,
    analyze_step_impact as build_step_impact,
    start_health_check_task,
)
from app.utils.response import ok

router = APIRouter(prefix="/impact", tags=["impact"])


@router.get("/elements/{element_id}", response_model=ApiResponse[ImpactResponse])
def analyze_element_impact(element_id: int, db: Session = Depends(get_db_session)):
    """Analyze element impact."""
    return ok(data=build_element_impact(db, element_id))


@router.get("/screens/{screen_id}", response_model=ApiResponse[ImpactResponse])
def analyze_screen_impact(screen_id: int, db: Session = Depends(get_db_session)):
    """Analyze screen impact."""
    return ok(data=build_screen_impact(db, screen_id))


@router.get("/steps/{step_id}", response_model=ApiResponse[ImpactResponse])
def analyze_step_impact(step_id: int, db: Session = Depends(get_db_session)):
    """Analyze step impact."""
    return ok(data=build_step_impact(db, step_id))


@router.get("/flows/{flow_id}", response_model=ApiResponse[ImpactResponse])
def analyze_flow_impact(flow_id: int, db: Session = Depends(get_db_session)):
    """Analyze flow impact."""
    return ok(data=build_flow_impact(db, flow_id))


@router.post("/health-check", response_model=ApiResponse[HealthCheckResponse])
def start_health_check(req: HealthCheckRequest, db: Session = Depends(get_db_session)):
    """Start element health check."""
    del req, db
    return ok(data=start_health_check_task(), message="Health check started")
