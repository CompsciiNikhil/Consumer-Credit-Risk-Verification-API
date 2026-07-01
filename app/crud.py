"""
crud.py — Database CRUD operations for CreditApplication records.
All deletes are soft deletes — records are never physically removed.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import ApplicationStatus, CreditApplication, RiskBand
from app.schemas import ApplicationCreate, ApplicationUpdate


def create_application(
    db: Session,
    data: ApplicationCreate,
    risk_score: float,
    risk_band: str,
) -> CreditApplication:
    """Persist a new credit application with pre-computed risk fields."""
    # Auto-flag if risk band is HIGH
    status = (
        ApplicationStatus.flagged
        if risk_band == RiskBand.HIGH.value
        else ApplicationStatus.pending
    )

    db_app = CreditApplication(
        applicant_name=data.applicant_name,
        annual_income=data.annual_income,
        existing_debt=data.existing_debt,
        credit_score=data.credit_score,
        loan_amount_requested=data.loan_amount_requested,
        employment_status=data.employment_status,
        risk_score=risk_score,
        risk_band=risk_band,
        status=status,
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app


def get_application(db: Session, application_id: int) -> Optional[CreditApplication]:
    """Fetch a single non-deleted application by ID."""
    return (
        db.query(CreditApplication)
        .filter(
            CreditApplication.id == application_id,
            CreditApplication.is_deleted == False,
        )
        .first()
    )


def get_applications(
    db: Session,
    status: Optional[str] = None,
    risk_band: Optional[str] = None,
) -> list[CreditApplication]:
    """List all non-deleted applications with optional status/risk_band filters."""
    query = db.query(CreditApplication).filter(CreditApplication.is_deleted == False)
    if status:
        query = query.filter(CreditApplication.status == status)
    if risk_band:
        query = query.filter(CreditApplication.risk_band == risk_band)
    return query.order_by(CreditApplication.created_at.desc()).all()


def update_application_status(
    db: Session,
    db_app: CreditApplication,
    data: ApplicationUpdate,
) -> CreditApplication:
    """Update an application's status (analyst review action)."""
    db_app.status = data.status
    db_app.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_app)
    return db_app


def soft_delete_application(
    db: Session,
    db_app: CreditApplication,
) -> None:
    """Soft-delete an application — sets is_deleted=True, never removes the row."""
    db_app.is_deleted = True
    db_app.updated_at = datetime.now(timezone.utc)
    db.commit()


def get_applications_by_risk_range(
    db: Session,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
) -> list[CreditApplication]:
    """
    Return non-deleted applications filtered by risk_score range,
    sorted by risk_score descending (highest risk first).
    """
    query = db.query(CreditApplication).filter(CreditApplication.is_deleted == False)
    if min_score is not None:
        query = query.filter(CreditApplication.risk_score >= min_score)
    if max_score is not None:
        query = query.filter(CreditApplication.risk_score <= max_score)
    return query.order_by(CreditApplication.risk_score.desc()).all()
