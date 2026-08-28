"""
Transaction & Telemetry Data Models for Pre-Auth Risk Evaluation
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class DeviceFingerprint(BaseModel):
    device_id: str
    ip_address: str
    user_agent: str
    canvas_hash: Optional[str] = None
    is_vpn: bool = False
    is_tor: bool = False
    is_emulator: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = "Unknown"
    country: Optional[str] = "IN"


class BehavioralBiometrics(BaseModel):
    typing_cadence_ms: float = 140.0         # Average keystroke interval
    paste_count: int = 0                     # Paste events in card/VPA field
    hesitation_seconds: float = 2.5          # Time before clicking submit
    screen_interaction_count: int = 12       # Pointer/Touch events count
    is_bot_pattern: bool = False


class TransactionPayload(BaseModel):
    transaction_id: str
    order_id: str
    user_id: str
    sender_vpa: Optional[str] = None         # e.g., 'rahul@okhdfcbank'
    receiver_vpa: Optional[str] = "merchant.payflow@razorpay"
    card_fingerprint: Optional[str] = None   # Hashed card token
    amount: float
    currency: str = "INR"
    payment_method: str = "upi"              # upi, card, netbanking, wallet
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    device: DeviceFingerprint
    behavior: BehavioralBiometrics = Field(default_factory=BehavioralBiometrics)
    metadata: Dict[str, Any] = Field(default_factory=dict)
