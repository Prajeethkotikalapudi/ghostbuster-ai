"""
API Integration Tests for GhostBuster AI Server Endpoints
"""

import unittest
from fastapi.testclient import TestClient
from main import app


class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_dashboard_root_endpoint(self):
        """GET / returns HTML Merchant Command Center."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("GhostBuster.AI", response.text)
        print("[PASS] GET / (Merchant Risk Command Center)")

    def test_02_evaluate_transaction_api(self):
        """POST /api/evaluate-transaction evaluates payment in real-time."""
        payload = {
            "transaction_id": "tx_api_001",
            "order_id": "order_api_001",
            "user_id": "user_api_clean",
            "sender_vpa": "api_user@okhdfcbank",
            "amount": 1999.0,
            "device": {
                "device_id": "dev_api_iphone",
                "ip_address": "103.21.14.82",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4)",
                "canvas_hash": "canvas_valid_1234",
                "city": "Mumbai"
            },
            "behavior": {
                "typing_cadence_ms": 140.0,
                "paste_count": 0,
                "hesitation_seconds": 2.0
            }
        }
        res = self.client.post("/api/evaluate-transaction", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "APPROVED")
        self.assertEqual(data["risk_report"]["decision"], "ALLOW")
        print(f"[PASS] POST /api/evaluate-transaction -> Status: {data['status']}, Risk: {data['risk_report']['risk_score']}/100")

    def test_03_graph_data_endpoint(self):
        """GET /api/graph-data returns Cytoscape nodes and edges."""
        res = self.client.get("/api/graph-data")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("elements", data)
        self.assertIn("investigation_summary", data)
        print(f"[PASS] GET /api/graph-data -> {len(data['elements'])} Cytoscape elements returned.")

    def test_04_simulate_attacks(self):
        """POST /api/simulate-attack runs live attack scenarios."""
        # 1. Card Testing Botnet
        res_bot = self.client.post("/api/simulate-attack", json={"attack_type": "card_testing_botnet"})
        self.assertEqual(res_bot.status_code, 200)
        self.assertEqual(res_bot.json()["status"], "ALL_INTERCEPTED")

        # 2. Impossible Travel
        res_travel = self.client.post("/api/simulate-attack", json={"attack_type": "impossible_travel"})
        self.assertEqual(res_travel.status_code, 200)
        self.assertEqual(res_travel.json()["status"], "INTERCEPTED")

        # 3. Mule Ring
        res_mule = self.client.post("/api/simulate-attack", json={"attack_type": "mule_ring_hopping"})
        self.assertEqual(res_mule.status_code, 200)
        self.assertEqual(res_mule.json()["status"], "BLOCKED_SYNDICATE_LINKAGE")

        # 4. Friendly Fraud
        res_disp = self.client.post("/api/simulate-attack", json={"attack_type": "friendly_fraud_dispute"})
        self.assertEqual(res_disp.status_code, 200)
        self.assertEqual(res_disp.json()["status"], "AUTO_DEFENSE_SUBMITTED")

        print("[PASS] POST /api/simulate-attack -> All 4 Attack Scenarios Successfully Executed.")

    def test_05_razorpay_webhook_dispute_creation(self):
        """POST /webhook/razorpay triggers automatic dispute defense dossier on dispute.created."""
        webhook_payload = {
            "event": "dispute.created",
            "payload": {
                "dispute": {
                    "entity": {
                        "id": "disp_test_webhook_01",
                        "payment_id": "pay_test_webhook_01",
                        "amount": 350000, # Rs. 3,500.00
                        "reason_code": "fraudulent"
                    }
                }
            }
        }
        res = self.client.post("/webhook/razorpay", json=webhook_payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "DISPUTE_DEFENSE_TRANSMITTED")
        print("[PASS] POST /webhook/razorpay -> Autonomous Chargeback Defense Triggered.")


if __name__ == "__main__":
    unittest.main()
