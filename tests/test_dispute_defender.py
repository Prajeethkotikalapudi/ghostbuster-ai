"""
Unit Tests for Dispute Defender Agent & Bank Evidence Dossier Generation
"""

import unittest
from agents.dispute_defender import dispute_defender_agent


class TestDisputeDefender(unittest.TestCase):

    def test_01_generate_evidence_dossier(self):
        """DisputeDefender generates a complete bank-compliant evidence packet with high winning probability."""
        dossier = dispute_defender_agent.generate_dispute_dossier(
            payment_id="pay_test_chargeback_88",
            order_id="order_test_cb_88",
            amount=4999.0,
            dispute_reason="unauthorized_transaction",
            customer_name="Amitabh Verma"
        )
        self.assertIsNotNone(dossier.dossier_id)
        self.assertGreaterEqual(dossier.winning_probability_pct, 90.0)
        self.assertIn("BlueDart", dossier.delivery_carrier_proof["courier"])
        self.assertTrue(len(dossier.session_audit_log) >= 3)
        self.assertIn("Scheme Rule 54(A)", dossier.ai_legal_brief)
        print(f"[PASS] Dispute Dossier Generated: ID: {dossier.dossier_id} -> Win Probability: {dossier.winning_probability_pct}%")


if __name__ == "__main__":
    unittest.main()
