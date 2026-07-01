"""
routers/applications.py — All 6 credit application endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.risk_engine import calculate_risk
from app.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    ErrorResponse,
)

router = APIRouter(prefix="/applications", tags=["Applications"])


# ---------------------------------------------------------------------------
# POST /applications — Create a new credit application
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a credit application",
)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    """
    Validate applicant data, compute risk score via the rule-based engine,
    and persist the record. Status is set to **flagged** if risk_band is HIGH,
    otherwise **pending**.
    """
    risk_score, risk_band = calculate_risk(
        annual_income=payload.annual_income,
        existing_debt=payload.existing_debt,
        credit_score=payload.credit_score,
        employment_status=payload.employment_status,
    )
    return crud.create_application(db, payload, risk_score, risk_band)


# ---------------------------------------------------------------------------
# GET /applications/risk-report — Must be defined BEFORE /{id} to avoid conflict
# ---------------------------------------------------------------------------
@router.get(
    "/risk-report",
    response_model=list[ApplicationResponse],
    summary="Filter applications by risk score range",
)
def risk_report(
    min_score: Optional[float] = Query(None, ge=0, le=100),
    max_score: Optional[float] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """
    Returns applications within the given risk_score range, sorted by
    risk_score descending (highest risk first).
    """
    if min_score is not None and max_score is not None and min_score > max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_score must be <= max_score",
        )
    return crud.get_applications_by_risk_range(db, min_score=min_score, max_score=max_score)


# ---------------------------------------------------------------------------
# GET /applications — List all (with optional filters)
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=list[ApplicationResponse],
    summary="List all credit applications",
)
def list_applications(
    app_status: Optional[str] = Query(None, alias="status"),
    risk_band: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Returns all non-deleted applications.
    Supports optional **status** and **risk_band** query filters.
    """
    return crud.get_applications(db, status=app_status, risk_band=risk_band)


# ---------------------------------------------------------------------------
# GET /applications/{id} — Get a single application
# ---------------------------------------------------------------------------
@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Get a credit application by ID",
)
def get_application(application_id: int, db: Session = Depends(get_db)):
    db_app = crud.get_application(db, application_id)
    if not db_app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )
    return db_app


# ---------------------------------------------------------------------------
# PUT /applications/{id}/review — Analyst review (update status)
# ---------------------------------------------------------------------------
@router.put(
    "/{application_id}/review",
    response_model=ApplicationResponse,
    summary="Analyst review — approve or reject an application",
)
def review_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
):
    """
    Simulates an analyst review action. Only **approved** and **rejected**
    are valid target statuses. Returns 400 for any other value.
    """
    db_app = crud.get_application(db, application_id)
    if not db_app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )
    return crud.update_application_status(db, db_app, payload)


# ---------------------------------------------------------------------------
# DELETE /applications/{id} — Soft delete
# ---------------------------------------------------------------------------
@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a credit application",
)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    """
    Marks the application as deleted (is_deleted=True).
    The record is never physically removed — mirrors financial data retention
    best practices.
    """
    db_app = crud.get_application(db, application_id)
    if not db_app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )
    crud.soft_delete_application(db, db_app)
