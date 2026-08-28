"""
GhostBuster AI Configuration & Environment Settings
"""

import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    APP_NAME: str = "GhostBuster AI - Autonomous Risk Manager"
    VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # Razorpay Fintech Credentials
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_ghostbuster_risk99")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "ghostbuster_secret_risk123")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "ghostbuster_webhook_sec_888")

    # Risk Thresholds
    RISK_THRESHOLD_ALLOW: float = 25.0       # <25 = 1-Click Zero Friction
    RISK_THRESHOLD_STEP_UP: float = 70.0     # 25-70 = Adaptive Challenge (OTP/Liveness)
                                             # >70 = Pre-Auth Block

    # Geolocation & Speed Limits
    MAX_PLAUSIBLE_SPEED_KMH: float = 850.0  # Commercial flight speed limit (~850-900 km/h)

    # Velocity Windows (Seconds)
    RAPID_BURST_WINDOW_SEC: int = 60
    BURST_TRANSACTION_LIMIT: int = 5


settings = Settings()
