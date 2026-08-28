"""
Risk Report & Vector Breakdown Schemas
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class RiskDecision(str, Enum):
    ALLOW = "ALLOW"             # Score < 25: Low Risk, 1-Click Instant Settlement
    STEP_UP = "STEP_UP"         # Score 25-70: Medium Risk, Adaptive Challenge (OTP/Liveness)
    BLOCK = "BLOCK"             # Score > 70: High Risk, Pre-Auth Intercept


class VectorScore(BaseModel):
    vector_name: str
    score: float                # 0.0 to 100.0
    weight: float               # Percentage contribution
    status: str                 # 'CLEAN', 'ELEVATED', 'CRITICAL'
    details: str


class PreAuthRiskReport(BaseModel):
    evaluation_id: str
    transaction_id: str
    order_id: str
    user_id: str
    risk_score: float           # Composite 0.0 to 100.0
    decision: RiskDecision
    recommended_action: str
    reason_codes: List[str]
    vector_breakdown: List[VectorScore]
    latency_ms: float
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    mule_syndicate_id: Optional[str] = None
    ai_risk_narrative: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
