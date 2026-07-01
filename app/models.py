"""
models.py — SQLAlchemy ORM models for the credit risk API.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, Integer, String
)
from sqlalchemy.orm import Mapped

from app.database import Base


class EmploymentStatus(str, enum.Enum):
    employed = "employed"
    self_employed = "self_employed"
    unemployed = "unemployed"


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    flagged = "flagged"


class RiskBand(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CreditApplication(Base):
    __tablename__ = "credit_applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    applicant_name = Column(String(100), nullable=False)
    annual_income = Column(Float, nullable=False)
    existing_debt = Column(Float, nullable=False, default=0.0)
    credit_score = Column(Integer, nullable=False)
    loan_amount_requested = Column(Float, nullable=False)
    employment_status = Column(Enum(EmploymentStatus), nullable=False)

    # Computed on creation by the risk engine
    risk_score = Column(Float, nullable=True)
    risk_band = Column(Enum(RiskBand), nullable=True)

    # Workflow status — auto-set to flagged if HIGH risk, else pending
    status = Column(
        Enum(ApplicationStatus),
        nullable=False,
        default=ApplicationStatus.pending,
    )

    # Soft delete — never hard-delete financial records
    is_deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
