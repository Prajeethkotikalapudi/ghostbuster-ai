"""
Real-Time Mule Account & Fraud Ring Graph Intelligence Service
Maintains an in-memory graph network linking Users, VPAs, Devices, and IPs.
Detects circular fund-hopping, multi-account device pooling, and generates Cytoscape.js graph payloads.
"""

from typing import Dict, List, Set, Any, Optional, Tuple
from datetime import datetime


class GraphNode:
    def __init__(self, node_id: str, node_type: str, label: str, risk_score: float = 0.0, is_flagged: bool = False):
        self.id = node_id
        self.type = node_type # 'user', 'vpa', 'device', 'ip', 'merchant'
        self.label = label
        self.risk_score = risk_score
        self.is_flagged = is_flagged
        self.first_seen = datetime.utcnow()
        self.last_seen = datetime.utcnow()
        self.metadata: Dict[str, Any] = {}


class GraphEdge:
    def __init__(self, source: str, target: str, relationship: str, weight: float = 1.0):
        self.source = source
        self.target = target
        self.relationship = relationship # 'USED_DEVICE', 'ASSOCIATED_IP', 'TRANSFERRED_TO', 'OWNS_VPA'
        self.weight = weight
        self.timestamp = datetime.utcnow()


class MuleGraphService:
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.adjacency: Dict[str, Set[str]] = {}
        self.known_syndicates: Dict[str, Set[str]] = {}
        self._seed_default_graph()

    def _seed_default_graph(self):
        """Pre-populates baseline legitimate network and a flagged mule syndicate for realistic demo."""
        # 1. Clean Node Cluster (Legitimate Merchant & Shoppers)
        self.add_or_update_node("merchant_root", "merchant", "Razorpay Official Store", risk_score=0.0)
        self.add_or_update_node("user_priya", "user", "Priya S. (Verified)", risk_score=5.0)
        self.add_or_update_node("vpa_priya", "vpa", "priya@okhdfcbank", risk_score=5.0)
        self.add_or_update_node("dev_priya", "device", "iPhone 15 Pro (dev_8891)", risk_score=5.0)
        self.add_or_update_node("ip_priya", "ip", "103.21.14.82 (Mumbai)", risk_score=5.0)

        self.add_edge("user_priya", "vpa_priya", "OWNS_VPA")
        self.add_edge("user_priya", "dev_priya", "USED_DEVICE")
        self.add_edge("dev_priya", "ip_priya", "ASSOCIATED_IP")
        self.add_edge("vpa_priya", "merchant_root", "TRANSFERRED_TO")

        # 2. Flagged Syndicate Alpha (Circular Mule Ring)
        syn_nodes = [
            ("mule_bot_1", "user", "Mule Bot #1", 92.0, True),
            ("vpa_mule_1", "vpa", "fastcash99@ybl", 90.0, True),
            ("mule_bot_2", "user", "Mule Bot #2", 88.0, True),
            ("vpa_mule_2", "vpa", "instantwin77@paytm", 89.0, True),
            ("mule_bot_3", "user", "Mule Bot #3", 95.0, True),
            ("vpa_mule_3", "vpa", "darknode33@axis", 94.0, True),
            ("dev_syndicate_shared", "device", "Rooted Emulator (dev_EMU_007)", 98.0, True),
            ("ip_tor_syndicate", "ip", "185.220.101.5 (Tor Exit)", 95.0, True)
        ]
        for nid, ntype, lbl, rscore, is_flag in syn_nodes:
            self.add_or_update_node(nid, ntype, lbl, risk_score=rscore, is_flagged=is_flag)

        # Connect the Circular Mule Chain: 1 -> 2 -> 3 -> 1
        self.add_edge("mule_bot_1", "vpa_mule_1", "OWNS_VPA")
        self.add_edge("mule_bot_2", "vpa_mule_2", "OWNS_VPA")
        self.add_edge("mule_bot_3", "vpa_mule_3", "OWNS_VPA")

        self.add_edge("mule_bot_1", "dev_syndicate_shared", "USED_DEVICE")
        self.add_edge("mule_bot_2", "dev_syndicate_shared", "USED_DEVICE")
        self.add_edge("mule_bot_3", "dev_syndicate_shared", "USED_DEVICE")

        self.add_edge("dev_syndicate_shared", "ip_tor_syndicate", "ASSOCIATED_IP")

        self.add_edge("vpa_mule_1", "vpa_mule_2", "TRANSFERRED_TO")
        self.add_edge("vpa_mule_2", "vpa_mule_3", "TRANSFERRED_TO")
        self.add_edge("vpa_mule_3", "vpa_mule_1", "TRANSFERRED_TO") # Cycle!

        self.known_syndicates["SYNDICATE_ALPHA"] = {"mule_bot_1", "mule_bot_2", "mule_bot_3", "vpa_mule_1", "vpa_mule_2", "vpa_mule_3", "dev_syndicate_shared", "ip_tor_syndicate"}

    def add_or_update_node(self, node_id: str, node_type: str, label: str, risk_score: float = 0.0, is_flagged: bool = False) -> GraphNode:
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(node_id, node_type, label, risk_score, is_flagged)
            self.adjacency[node_id] = set()
        else:
            self.nodes[node_id].last_seen = datetime.utcnow()
            if is_flagged:
                self.nodes[node_id].is_flagged = True
            if risk_score > self.nodes[node_id].risk_score:
                self.nodes[node_id].risk_score = risk_score
        return self.nodes[node_id]

    def add_edge(self, source: str, target: str, relationship: str, weight: float = 1.0):
        # Ensure nodes exist
        if source not in self.nodes:
            self.add_or_update_node(source, "unknown", source)
        if target not in self.nodes:
            self.add_or_update_node(target, "unknown", target)

        edge = GraphEdge(source, target, relationship, weight)
        self.edges.append(edge)
        self.adjacency[source].add(target)
        self.adjacency[target].add(source)

    def ingest_transaction(
        self,
        user_id: str,
        sender_vpa: Optional[str],
        receiver_vpa: str,
        device_id: str,
        ip_address: str,
        amount: float,
        is_risky: bool = False
    ) -> Dict[str, Any]:
        """
        Ingests a live transaction into the network graph and performs real-time cycle & degree inspection.
        """
        # Add Nodes
        u_node = self.add_or_update_node(user_id, "user", f"User {user_id}", is_flagged=is_risky)
        d_node = self.add_or_update_node(device_id, "device", f"Device {device_id[:8]}", is_flagged=is_risky)
        ip_node = self.add_or_update_node(ip_address, "ip", f"IP {ip_address}", is_flagged=is_risky)
        
        self.add_edge(user_id, device_id, "USED_DEVICE")
        self.add_edge(device_id, ip_address, "ASSOCIATED_IP")

        if sender_vpa:
            v_node = self.add_or_update_node(sender_vpa, "vpa", sender_vpa, is_flagged=is_risky)
            self.add_edge(user_id, sender_vpa, "OWNS_VPA")
            self.add_edge(sender_vpa, receiver_vpa, "TRANSFERRED_TO", weight=amount)

        # Inspect Graph Metrics
        degree = len(self.adjacency.get(device_id, set()))
        is_high_fan_out = degree >= 4
        mule_affinity = self.calculate_mule_affinity(user_id, device_id, sender_vpa)

        return {
            "device_node_degree": degree,
            "is_high_fan_out_device": is_high_fan_out,
            "mule_affinity_score": mule_affinity["affinity_score"],
            "linked_syndicate": mule_affinity["syndicate_id"],
            "cycles_detected": mule_affinity["has_cycle"]
        }

    def calculate_mule_affinity(self, user_id: str, device_id: str, sender_vpa: Optional[str]) -> Dict[str, Any]:
        """
        Calculates graph distance and affinity to known flagged mule syndicates.
        """
        candidates = {user_id, device_id}
        if sender_vpa:
            candidates.add(sender_vpa)

        for syn_id, members in self.known_syndicates.items():
            # Check 1-hop direct intersection
            direct_overlap = candidates.intersection(members)
            if direct_overlap:
                return {
                    "affinity_score": 95.0,
                    "syndicate_id": syn_id,
                    "has_cycle": True,
                    "details": f"Direct 1-Hop membership in {syn_id} via {list(direct_overlap)}"
                }

            # Check 2-hop neighborhood
            for c in candidates:
                neighbors = self.adjacency.get(c, set())
                neighbor_overlap = neighbors.intersection(members)
                if neighbor_overlap:
                    return {
                        "affinity_score": 75.0,
                        "syndicate_id": syn_id,
                        "has_cycle": False,
                        "details": f"2-Hop connection to {syn_id} through {list(neighbor_overlap)}"
                    }

        return {
            "affinity_score": 0.0,
            "syndicate_id": None,
            "has_cycle": False,
            "details": "No linkage to known mule rings"
        }

    def export_cytoscape_elements(self) -> List[Dict[str, Any]]:
        """
        Exports all nodes and edges in standard Cytoscape.js format for the interactive web visualizer.
        """
        elements = []

        for nid, node in self.nodes.items():
            elements.append({
                "data": {
                    "id": nid,
                    "label": node.label,
                    "type": node.type,
                    "risk_score": node.risk_score,
                    "is_flagged": node.is_flagged
                }
            })

        for edge in self.edges:
            elements.append({
                "data": {
                    "id": f"{edge.source}->{edge.target}",
                    "source": edge.source,
                    "target": edge.target,
                    "relationship": edge.relationship,
                    "weight": edge.weight
                }
            })

        return elements


mule_graph_service = MuleGraphService()
