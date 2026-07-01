"""
schemas.py — Pydantic request/response schemas with full input validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models import ApplicationStatus, EmploymentStatus, RiskBand


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ApplicationCreate(BaseModel):
    applicant_name: str = Field(..., min_length=1, max_length=100)
    annual_income: float = Field(..., gt=0, description="Must be greater than 0")
    existing_debt: float = Field(0.0, ge=0, description="Must be >= 0")
    credit_score: int = Field(..., ge=300, le=850, description="FICO range 300–850")
    loan_amount_requested: float = Field(..., gt=0, description="Must be greater than 0")
    employment_status: EmploymentStatus

    model_config = {"use_enum_values": True}


class ApplicationUpdate(BaseModel):
    """Used by the analyst review endpoint — only status can be changed."""
    status: ApplicationStatus

    model_config = {"use_enum_values": True}

    @field_validator("status")
    @classmethod
    def status_must_be_reviewable(cls, v):
        allowed = {ApplicationStatus.approved.value, ApplicationStatus.rejected.value}
        if v not in allowed:
            raise ValueError(
                f"Review endpoint only accepts status: {', '.join(allowed)}"
            )
        return v


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class ApplicationResponse(BaseModel):
    id: int
    applicant_name: str
    annual_income: float
    existing_debt: float
    credit_score: int
    loan_amount_requested: float
    employment_status: str
    status: str
    risk_score: Optional[float]
    risk_band: Optional[str]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Structured error response
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    error: str
    detail: str
