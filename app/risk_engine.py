"""
risk_engine.py — Pure, rule-based credit risk scoring engine.

This module contains NO database or API dependencies — it is a pure function
that can be unit-tested completely in isolation.

Scoring Formula
---------------
risk_score is a float in the range [0, 100], where higher = riskier.

Three weighted components:

  1. Credit Score Band           — weight: 40%
     740+          →  5  points  (LOW)
     670–739       → 20  points  (LOW-MEDIUM)
     580–669       → 50  points  (MEDIUM)
     < 580         → 85  points  (HIGH)

  2. Debt-to-Income (DTI) Ratio  — weight: 35%
     DTI < 0.30    →  5  points  (LOW)
     DTI 0.30–0.50 → 45  points  (MEDIUM)
     DTI > 0.50    → 90  points  (HIGH)

  3. Employment Status            — weight: 25%
     employed      →  5  points  (LOW)
     self_employed → 45  points  (MEDIUM)
     unemployed    → 90  points  (HIGH)

Final formula:
  risk_score = (credit_component * 0.40)
             + (dti_component    * 0.35)
             + (employment_component * 0.25)

Risk band mapping:
   0–33  → LOW
  34–66  → MEDIUM
  67–100 → HIGH
"""

from typing import Tuple


def _credit_score_component(credit_score: int) -> float:
    """Map a FICO-range credit score to a risk component (0–100, higher = riskier)."""
    if credit_score >= 740:
        return 5.0
    elif credit_score >= 670:
        return 20.0
    elif credit_score >= 580:
        return 50.0
    else:
        return 85.0


def _dti_component(annual_income: float, existing_debt: float) -> float:
    """
    Compute the debt-to-income component.
    DTI = existing_debt / annual_income.
    Returns a risk component (0–100, higher = riskier).
    """
    if annual_income <= 0:
        return 90.0  # defensive: treat zero income as maximum DTI risk
    dti = existing_debt / annual_income
    if dti < 0.30:
        return 5.0
    elif dti <= 0.50:
        return 45.0
    else:
        return 90.0


def _employment_component(employment_status: str) -> float:
    """Map employment status to a risk component (0–100, higher = riskier)."""
    mapping = {
        "employed": 5.0,
        "self_employed": 45.0,
        "unemployed": 90.0,
    }
    return mapping.get(employment_status, 90.0)


def calculate_risk(
    annual_income: float,
    existing_debt: float,
    credit_score: int,
    employment_status: str,
) -> Tuple[float, str]:
    """
    Calculate a transparent, rule-based risk score for a credit application.

    Parameters
    ----------
    annual_income       : Applicant's gross annual income (must be > 0).
    existing_debt       : Total outstanding debt obligations (>= 0).
    credit_score        : FICO-range credit score (300–850).
    employment_status   : One of 'employed', 'self_employed', 'unemployed'.

    Returns
    -------
    (risk_score, risk_band)
        risk_score : float in [0.0, 100.0] — higher means riskier.
        risk_band  : str — one of 'LOW', 'MEDIUM', 'HIGH'.
    """
    credit_component = _credit_score_component(credit_score)
    dti_component = _dti_component(annual_income, existing_debt)
    employment_component = _employment_component(employment_status)

    risk_score = (
        credit_component     * 0.40
        + dti_component      * 0.35
        + employment_component * 0.25
    )

    # Clamp to [0, 100] for safety
    risk_score = max(0.0, min(100.0, round(risk_score, 2)))

    if risk_score <= 33.0:
        risk_band = "LOW"
    elif risk_score <= 66.0:
        risk_band = "MEDIUM"
    else:
        risk_band = "HIGH"

    return risk_score, risk_band
