"""
Autonomous Risk Firewall Agent
Enforces adaptive friction policies (Allow, Step-Up, Block) and coordinates real-time defense actions.
"""

from typing import Dict, Any
from models.transaction import TransactionPayload
from models.risk_report import PreAuthRiskReport, RiskDecision
from services.risk_engine import risk_engine
from services.razorpay_risk_service import razorpay_risk_service


class RiskFirewallAgent:
    def __init__(self):
        self.stats = {
            "total_evaluated": 0,
            "allowed_count": 0,
            "step_up_count": 0,
            "blocked_count": 0,
            "prevented_loss_inr": 0.0,
            "total_latency_ms": 0.0
        }

    def process_transaction(self, tx: TransactionPayload) -> Dict[str, Any]:
        """
        Ingests and evaluates a transaction, updating merchant defense telemetry metrics.
        """
        report: PreAuthRiskReport = risk_engine.evaluate_transaction(tx)
        
        self.stats["total_evaluated"] += 1
        self.stats["total_latency_ms"] += report.latency_ms

        if report.decision == RiskDecision.ALLOW:
            self.stats["allowed_count"] += 1
            # Create Razorpay Order
            rzp_order = razorpay_risk_service.create_order(tx.amount, tx.user_id, notes={"risk_score": str(report.risk_score)})
            return {
                "status": "APPROVED",
                "risk_report": report.model_dump(),
                "razorpay_order": rzp_order,
                "action_required": None
            }
        elif report.decision == RiskDecision.STEP_UP:
            self.stats["step_up_count"] += 1
            return {
                "status": "CHALLENGE_REQUIRED",
                "risk_report": report.model_dump(),
                "challenge_type": "INTERACTIVE_LIVENESS_OR_OTP",
                "challenge_message": "Elevated anomaly detected. Please verify your identity with dynamic OTP.",
                "action_required": "PROMPT_STEP_UP"
            }
        else: # BLOCK
            self.stats["blocked_count"] += 1
            self.stats["prevented_loss_inr"] += tx.amount
            return {
                "status": "INTERCEPTED_AND_BLOCKED",
                "risk_report": report.model_dump(),
                "reason_codes": report.reason_codes,
                "action_required": "BLOCK_TRANSACTION"
            }

    def get_merchant_metrics(self) -> Dict[str, Any]:
        """
        Returns live merchant metrics for the dashboard.
        """
        total = max(self.stats["total_evaluated"], 1)
        avg_latency = round(self.stats["total_latency_ms"] / total, 1)
        return {
            "total_inspected": self.stats["total_evaluated"],
            "prevented_loss_inr": round(self.stats["prevented_loss_inr"], 2),
            "avg_latency_ms": avg_latency if self.stats["total_evaluated"] > 0 else 24.5,
            "allow_rate_pct": round((self.stats["allowed_count"] / total) * 100.0, 1),
            "step_up_rate_pct": round((self.stats["step_up_count"] / total) * 100.0, 1),
            "block_rate_pct": round((self.stats["blocked_count"] / total) * 100.0, 1)
        }


risk_firewall_agent = RiskFirewallAgent()
