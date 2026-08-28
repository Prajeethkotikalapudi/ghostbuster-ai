"""
Unit Tests for GhostBuster AI Pre-Auth Risk Engine
"""

import unittest
from datetime import datetime
from models.transaction import TransactionPayload, DeviceFingerprint, BehavioralBiometrics
from models.risk_report import RiskDecision
from services.risk_engine import risk_engine


class TestRiskEngine(unittest.TestCase):

    def test_01_clean_legitimate_transaction(self):
        """Legitimate shopper on residential IP with natural biometrics should get ALLOW decision."""
        tx = TransactionPayload(
            transaction_id="tx_test_clean_01",
            order_id="order_clean_01",
            user_id="user_priya_clean",
            sender_vpa="priya@okhdfcbank",
            amount=2499.0,
            device=DeviceFingerprint(
                device_id="dev_clean_iphone",
                ip_address="103.21.14.82",
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_4)",
                canvas_hash="canvas_valid_9981",
                city="Mumbai",
                country="IN"
            ),
            behavior=BehavioralBiometrics(
                typing_cadence_ms=145.0,
                paste_count=0,
                hesitation_seconds=2.4
            )
        )
        report = risk_engine.evaluate_transaction(tx)
        self.assertEqual(report.decision, RiskDecision.ALLOW)
        self.assertLess(report.risk_score, 25.0)
        self.assertLess(report.latency_ms, 50.0)
        print(f"[PASS] Clean Transaction -> Score: {report.risk_score}/100 ({report.decision.value}) in {report.latency_ms}ms")

    def test_02_card_probing_botnet_block(self):
        """Rapid micro-transaction bot on Tor network must be BLOCKED with reason codes."""
        bot_device = "dev_bot_tor_99"
        
        # Simulate 5 rapid bursts
        for i in range(5):
            tx = TransactionPayload(
                transaction_id=f"tx_bot_{i}",
                order_id=f"order_bot_{i}",
                user_id=f"bot_attacker_{i}",
                sender_vpa="card_tester@axis",
                amount=2.0, # Micro-probing
                device=DeviceFingerprint(
                    device_id=bot_device,
                    ip_address="185.220.101.5",
                    user_agent="HeadlessChrome/120.0.0.0",
                    is_tor=True
                ),
                behavior=BehavioralBiometrics(
                    typing_cadence_ms=10.0,
                    paste_count=5,
                    hesitation_seconds=0.02,
                    is_bot_pattern=True
                )
            )
            report = risk_engine.evaluate_transaction(tx)

        self.assertEqual(report.decision, RiskDecision.BLOCK)
        self.assertGreaterEqual(report.risk_score, 80.0)
        self.assertIn("TOR_ANONYMIZED_NETWORK", report.reason_codes)
        print(f"[PASS] Card Testing Bot Blocked -> Score: {report.risk_score}/100 ({report.decision.value}) Reasons: {report.reason_codes}")

    def test_03_vpn_adaptive_step_up_challenge(self):
        """Transaction on commercial VPN with moderate amount should trigger STEP_UP."""
        tx = TransactionPayload(
            transaction_id="tx_vpn_stepup",
            order_id="order_vpn_01",
            user_id="user_vpn_test",
            sender_vpa="shivam@paytm",
            amount=15000.0,
            device=DeviceFingerprint(
                device_id="dev_laptop_shivam",
                ip_address="84.17.45.12",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                is_vpn=True,
                city="Frankfurt"
            ),
            behavior=BehavioralBiometrics(
                typing_cadence_ms=120.0,
                paste_count=1,
                hesitation_seconds=1.5
            )
        )
        report = risk_engine.evaluate_transaction(tx)
        self.assertIn(report.decision, [RiskDecision.STEP_UP, RiskDecision.BLOCK])
        print(f"[PASS] VPN Anomaly -> Score: {report.risk_score}/100 ({report.decision.value}) Action: {report.recommended_action}")


if __name__ == "__main__":
    unittest.main()
