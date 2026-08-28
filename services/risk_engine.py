"""
High-Performance Pre-Auth Risk Engine (<50ms Latency)
Combines 6 orthogonal vector evaluations into a deterministic, explainable risk score and decision.
"""

import time
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from models.transaction import TransactionPayload
from models.risk_report import PreAuthRiskReport, RiskDecision, VectorScore
from services.geo_velocity import geo_velocity_service
from services.device_fingerprint import device_fingerprint_service
from services.graph_service import mule_graph_service
from config import settings


class RiskEngine:
    def __init__(self):
        # User transaction history cache for velocity tracking: {user_id: [timestamps...]}
        self.user_history: Dict[str, List[Dict[str, Any]]] = {}
        # Device transaction history: {device_id: [timestamps...]}
        self.device_history: Dict[str, List[datetime]] = {}
        # IP transaction history: {ip_address: [timestamps...]}
        self.ip_history: Dict[str, List[datetime]] = {}

    def evaluate_transaction(self, tx: TransactionPayload) -> PreAuthRiskReport:
        """
        Executes real-time multi-vector pre-authorization risk inspection in <50ms.
        """
        start_time = time.perf_counter()
        now = tx.timestamp or datetime.utcnow()
        reason_codes: List[str] = []
        vectors: List[VectorScore] = []

        # ================= VECTOR 1: DEVICE & NETWORK (Weight: 20%) =================
        dev_res = device_fingerprint_service.evaluate_fingerprint(tx.device)
        dev_score = dev_res["device_risk_score"]
        dev_status = "CRITICAL" if dev_score >= 70 else ("ELEVATED" if dev_score >= 35 else "CLEAN")
        if dev_res["flags"]:
            reason_codes.extend(dev_res["flags"])
        
        vectors.append(VectorScore(
            vector_name="Device & Network Reputation",
            score=dev_score,
            weight=0.20,
            status=dev_status,
            details=f"Flags: {', '.join(dev_res['flags']) if dev_res['flags'] else 'Authentic Device & Residential IP'}"
        ))

        # ================= VECTOR 2: GEO-VELOCITY / IMPOSSIBLE TRAVEL (Weight: 25%) =================
        geo_score = 0.0
        geo_details = "First transaction / Normal velocity"
        
        user_past_txs = self.user_history.get(tx.user_id, [])
        if user_past_txs:
            last_tx = user_past_txs[-1]
            geo_res = geo_velocity_service.calculate_velocity(
                prev_lat=last_tx.get("lat"),
                prev_lon=last_tx.get("lon"),
                prev_time=last_tx.get("time"),
                curr_lat=tx.device.latitude,
                curr_lon=tx.device.longitude,
                curr_time=now
            )
            if geo_res["is_impossible_travel"]:
                geo_score = 95.0
                reason_codes.append("IMPOSSIBLE_GEO_VELOCITY_ANOMALY")
                geo_details = f"Impossible speed: {geo_res['velocity_kmh']} km/h ({geo_res['distance_km']} km in {geo_res['time_delta_minutes']} mins)"
            elif geo_res["velocity_kmh"] > 400.0:
                geo_score = 45.0
                reason_codes.append("ELEVATED_TRAVEL_SPEED")
                geo_details = f"Rapid speed: {geo_res['velocity_kmh']} km/h"

        geo_status = "CRITICAL" if geo_score >= 70 else ("ELEVATED" if geo_score >= 35 else "CLEAN")
        vectors.append(VectorScore(
            vector_name="Geo-Velocity Anomaly",
            score=geo_score,
            weight=0.25,
            status=geo_status,
            details=geo_details
        ))

        # ================= VECTOR 3: BEHAVIORAL BIOMETRICS (Weight: 15%) =================
        beh_score = 0.0
        beh_flags = []
        if tx.behavior.is_bot_pattern:
            beh_score += 90.0
            beh_flags.append("BOT_INTERACTION_SIGNATURE")
        if tx.behavior.paste_count >= 3:
            beh_score += 40.0
            beh_flags.append("AUTOMATED_PASTE_BURST")
        if tx.behavior.hesitation_seconds < 0.2:
            beh_score += 50.0
            beh_flags.append("ZERO_HESITATION_SCRIPTED_CLICK")
        elif tx.behavior.typing_cadence_ms < 20.0:
            beh_score += 60.0
            beh_flags.append("SUPERHUMAN_KEYSTROKE_SPEED")

        beh_score = min(beh_score, 100.0)
        beh_status = "CRITICAL" if beh_score >= 70 else ("ELEVATED" if beh_score >= 35 else "CLEAN")
        if beh_flags:
            reason_codes.extend(beh_flags)

        vectors.append(VectorScore(
            vector_name="Behavioral Biometrics",
            score=beh_score,
            weight=0.15,
            status=beh_status,
            details=f"Cadence: {tx.behavior.typing_cadence_ms}ms, Pastes: {tx.behavior.paste_count}, Flags: {', '.join(beh_flags) if beh_flags else 'Natural Human'}"
        ))

        # ================= VECTOR 4: TRANSACTION VELOCITY & BURST (Weight: 20%) =================
        dev_history = self.device_history.get(tx.device.device_id, [])
        cutoff_1m = now - timedelta(seconds=60)
        recent_burst_count = sum(1 for t in dev_history if t >= cutoff_1m)

        vel_score = 0.0
        if recent_burst_count >= 10:
            vel_score = 100.0
            reason_codes.append("HIGH_FREQUENCY_CARD_PROBING_BOTNET")
        elif recent_burst_count >= 4:
            vel_score = 65.0
            reason_codes.append("RAPID_TRANSACTION_BURST")

        vel_status = "CRITICAL" if vel_score >= 70 else ("ELEVATED" if vel_score >= 35 else "CLEAN")
        vectors.append(VectorScore(
            vector_name="Velocity & Probing",
            score=vel_score,
            weight=0.20,
            status=vel_status,
            details=f"{recent_burst_count} transactions in last 60s from device"
        ))

        # ================= VECTOR 5: MULE GRAPH AFFINITY (Weight: 15%) =================
        graph_res = mule_graph_service.ingest_transaction(
            user_id=tx.user_id,
            sender_vpa=tx.sender_vpa,
            receiver_vpa=tx.receiver_vpa,
            device_id=tx.device.device_id,
            ip_address=tx.device.ip_address,
            amount=tx.amount,
            is_risky=(dev_score > 60 or geo_score > 60)
        )
        mule_score = graph_res["mule_affinity_score"]
        if graph_res["is_high_fan_out_device"]:
            mule_score = max(mule_score, 60.0)
            reason_codes.append("MULTI_ACCOUNT_DEVICE_POOLING")
        if graph_res["cycles_detected"]:
            mule_score = 95.0
            reason_codes.append("CIRCULAR_MULE_FUND_HOPPING")

        mule_status = "CRITICAL" if mule_score >= 70 else ("ELEVATED" if mule_score >= 35 else "CLEAN")
        vectors.append(VectorScore(
            vector_name="Mule Ring Affinity",
            score=mule_score,
            weight=0.15,
            status=mule_status,
            details=f"Syndicate Link: {graph_res['linked_syndicate'] or 'None'} | Fan-Out: {graph_res['device_node_degree']} accounts"
        ))

        # ================= VECTOR 6: AMOUNT ANOMALY & PROBING (Weight: 5%) =================
        amt_score = 0.0
        if tx.amount <= 10.0 and recent_burst_count >= 2:
            amt_score = 80.0
            reason_codes.append("MICRO_AMOUNT_AUTHORIZATION_PROBING")
        elif tx.amount > 100000.0 and len(user_past_txs) < 2:
            amt_score = 50.0
            reason_codes.append("HIGH_VALUE_FIRST_TIME_ANOMALY")

        amt_status = "CRITICAL" if amt_score >= 70 else ("ELEVATED" if amt_score >= 35 else "CLEAN")
        vectors.append(VectorScore(
            vector_name="Amount Anomaly",
            score=amt_score,
            weight=0.05,
            status=amt_status,
            details=f"Amount: ₹{tx.amount:,.2f}"
        ))

        # ================= COMPOSITE RISK SCORE CALCULATION =================
        composite_score = sum(v.score * v.weight for v in vectors)
        
        # Security Risk Floors:
        # 1. Tor / Headless Bot / Impossible Travel / Probing Botnet -> Immediate BLOCK (>75.0)
        if (
            geo_score >= 90.0 or
            "TOR_ANONYMIZED_NETWORK" in reason_codes or
            "BOT_INTERACTION_SIGNATURE" in reason_codes or
            "AUTOMATED_HEADLESS_BOTNET" in reason_codes or
            "CIRCULAR_MULE_FUND_HOPPING" in reason_codes or
            "HIGH_FREQUENCY_CARD_PROBING_BOTNET" in reason_codes or
            vel_score >= 65.0
        ):
            composite_score = max(composite_score, 88.0)
        
        # 2. Commercial VPN / Emulator / Device Spoofing -> Minimum STEP_UP (>= 35.0)
        elif (
            "ANONYMOUS_VPN_DETECTED" in reason_codes or
            "DEVICE_EMULATOR_SPOOFING" in reason_codes or
            "ELEVATED_TRAVEL_SPEED" in reason_codes or
            "AUTOMATED_PASTE_BURST" in reason_codes
        ):
            composite_score = max(composite_score, 38.0)

        composite_score = round(min(max(composite_score, 0.0), 100.0), 1)

        # Decision Gate
        if composite_score < settings.RISK_THRESHOLD_ALLOW:
            decision = RiskDecision.ALLOW
            action = "1-Click Instant Authorization (Zero Friction)"
        elif composite_score <= settings.RISK_THRESHOLD_STEP_UP:
            decision = RiskDecision.STEP_UP
            action = "Trigger Adaptive Step-Up Auth (Interactive Liveness / Dynamic OTP)"
        else:
            decision = RiskDecision.BLOCK
            action = "Pre-Auth Intercept: Declined with Risk Reason Codes"

        # Update History Caches
        if tx.user_id not in self.user_history:
            self.user_history[tx.user_id] = []
        self.user_history[tx.user_id].append({
            "time": now,
            "lat": tx.device.latitude,
            "lon": tx.device.longitude,
            "amount": tx.amount
        })

        if tx.device.device_id not in self.device_history:
            self.device_history[tx.device.device_id] = []
        self.device_history[tx.device.device_id].append(now)

        if tx.device.ip_address not in self.ip_history:
            self.ip_history[tx.device.ip_address] = []
        self.ip_history[tx.device.ip_address].append(now)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # AI Narrative Explanation
        narrative = self._generate_ai_narrative(composite_score, decision, reason_codes, tx)

        return PreAuthRiskReport(
            evaluation_id=f"eval_{uuid.uuid4().hex[:12]}",
            transaction_id=tx.transaction_id,
            order_id=tx.order_id,
            user_id=tx.user_id,
            risk_score=composite_score,
            decision=decision,
            recommended_action=action,
            reason_codes=list(set(reason_codes)),
            vector_breakdown=vectors,
            latency_ms=elapsed_ms,
            evaluated_at=now,
            mule_syndicate_id=graph_res["linked_syndicate"],
            ai_risk_narrative=narrative
        )

    def _generate_ai_narrative(self, score: float, decision: RiskDecision, reasons: List[str], tx: TransactionPayload) -> str:
        if decision == RiskDecision.ALLOW:
            return f"Transaction is verified clean (Risk: {score}/100). Valid residential IP, natural biometric typing cadence, and zero mule ring linkages detected."
        elif decision == RiskDecision.STEP_UP:
            return f"Elevated anomaly detected (Risk: {score}/100) due to: {', '.join(reasons) if reasons else 'mild heuristic variance'}. Recommending dynamic step-up challenge before settlement."
        else:
            return f"CRITICAL SECURITY ALERT (Risk: {score}/100). Intercepted pre-auth transaction for ₹{tx.amount:,.2f}. Triggered triggers: {', '.join(reasons)}. Potential mule syndicate or bot attack."


risk_engine = RiskEngine()
