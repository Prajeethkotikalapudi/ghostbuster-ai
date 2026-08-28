"""
Bank Chargeback Dispute Evidence Packet Model
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AuditEvent(BaseModel):
    timestamp: datetime
    event_type: str
    description: str
    ip_address: Optional[str] = None
    device_id: Optional[str] = None


class DisputeEvidencePacket(BaseModel):
    dossier_id: str
    dispute_id: str
    payment_id: str
    order_id: str
    disputed_amount: float
    dispute_reason: str                      # 'unauthorized_transaction', 'product_not_received', 'fraudulent'
    customer_name: str
    customer_email: str
    customer_phone: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Evidence Dossier Sections
    risk_assessment_summary: str
    device_fingerprint_evidence: Dict[str, Any]
    geolocation_audit_trail: Dict[str, Any]
    behavioral_biometrics_proof: Dict[str, Any]
    signed_invoice_url: str
    delivery_carrier_proof: Dict[str, Any]
    session_audit_log: List[AuditEvent]
    
    # AI Legal Defense Brief
    ai_legal_brief: str
    winning_probability_pct: float
    status: str = "SUBMITTED_TO_RAZORPAY"
