"""
Unit Tests for Real-Time Mule Account & Fraud Ring Graph Service
"""

import unittest
from services.graph_service import mule_graph_service
from agents.mule_hunter_agent import mule_hunter_agent


class TestMuleGraph(unittest.TestCase):

    def test_01_syndicate_cycle_detection(self):
        """Mule Syndicate Alpha (circular VPA ring) must be identified and flagged."""
        inv = mule_hunter_agent.run_syndicate_investigation()
        self.assertGreaterEqual(inv["active_syndicates_detected"], 1)
        self.assertGreaterEqual(inv["flagged_mule_nodes"], 3)
        print(f"[PASS] Syndicate Graph Traversal: Detected {inv['active_syndicates_detected']} syndicate rings with {inv['flagged_mule_nodes']} flagged nodes.")

    def test_02_direct_syndicate_affinity_matching(self):
        """Transaction attempting to route via known syndicate node triggers high affinity."""
        res = mule_graph_service.ingest_transaction(
            user_id="mule_bot_1",
            sender_vpa="fastcash99@ybl",
            receiver_vpa="instantwin77@paytm",
            device_id="dev_syndicate_shared",
            ip_address="185.220.101.5",
            amount=50000.0,
            is_risky=True
        )
        self.assertEqual(res["linked_syndicate"], "SYNDICATE_ALPHA")
        self.assertGreaterEqual(res["mule_affinity_score"], 90.0)
        self.assertTrue(res["cycles_detected"])
        print(f"[PASS] Syndicate Affinity Match -> Score: {res['mule_affinity_score']}/100, Syndicate: {res['linked_syndicate']}")

    def test_03_cytoscape_export_integrity(self):
        """Cytoscape elements export must contain valid nodes and edges."""
        elements = mule_graph_service.export_cytoscape_elements()
        self.assertTrue(len(elements) > 5)
        
        nodes = [e for e in elements if "source" not in e["data"]]
        edges = [e for e in elements if "source" in e["data"]]
        self.assertTrue(len(nodes) > 0)
        self.assertTrue(len(edges) > 0)
        print(f"[PASS] Cytoscape Export Verified: {len(nodes)} Nodes, {len(edges)} Edges.")


if __name__ == "__main__":
    unittest.main()
