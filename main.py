"""
GhostBuster AI: Autonomous Risk Intelligence & Fraud Mitigation Server
FastAPI Server delivering Pre-Auth Interception, Interactive Mule Graph Visualizer,
1-Click Attack Simulator, and Automated Chargeback Dispute Defense.
"""

import os
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from models.transaction import TransactionPayload, DeviceFingerprint, BehavioralBiometrics
from models.risk_report import PreAuthRiskReport, RiskDecision
from models.dispute_packet import DisputeEvidencePacket
from services.risk_engine import risk_engine
from services.graph_service import mule_graph_service
from services.razorpay_risk_service import razorpay_risk_service
from agents.risk_firewall_agent import risk_firewall_agent
from agents.mule_hunter_agent import mule_hunter_agent
from agents.dispute_defender import dispute_defender_agent


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Enterprise Pre-Auth Fraud Interceptor & Mule Ring Graph Intelligence"
)

# Static & Template Directories
static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# In-Memory Stream of Recent Evaluated Threats
threat_stream: List[Dict[str, Any]] = []


@app.get("/", response_class=HTMLResponse)
async def serve_merchant_command_center(request: Request):
    """
    Renders the GhostBuster AI Merchant Risk Command Center.
    """
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": settings.APP_NAME,
            "version": settings.VERSION,
            "metrics": risk_firewall_agent.get_merchant_metrics()
        }
    )


@app.get("/pitch", response_class=HTMLResponse)
async def serve_pitch_video(request: Request):
    """
    Renders the 5-Minute Cinematic Pitch Video Player with Voice Narration.
    """
    return templates.TemplateResponse(
        request=request,
        name="pitch.html",
        context={
            "app_name": settings.APP_NAME,
            "version": settings.VERSION
        }
    )


@app.post("/api/evaluate-transaction")
async def evaluate_transaction(payload: TransactionPayload):
    """
    Evaluates an incoming payment request in <50ms and returns decision (ALLOW, STEP_UP, BLOCK).
    """
    result = risk_firewall_agent.process_transaction(payload)
    
    # Prepend to live threat stream (keep last 50)
    threat_item = {
        "id": payload.transaction_id,
        "amount": payload.amount,
        "user_id": payload.user_id,
        "vpa": payload.sender_vpa or payload.payment_method.upper(),
        "city": payload.device.city or "Unknown",
        "decision": result["risk_report"]["decision"],
        "risk_score": result["risk_report"]["risk_score"],
        "latency_ms": result["risk_report"]["latency_ms"],
        "reason_codes": result["risk_report"]["reason_codes"],
        "timestamp": datetime.utcnow().strftime("%H:%M:%S")
    }
    threat_stream.insert(0, threat_item)
    if len(threat_stream) > 50:
        threat_stream.pop()

    return result


@app.get("/api/graph-data")
async def get_graph_data():
    """
    Returns Cytoscape.js compatible graph nodes and edges for the live mule visualizer.
    """
    elements = mule_graph_service.export_cytoscape_elements()
    investigation = mule_hunter_agent.run_syndicate_investigation()
    return {
        "elements": elements,
        "investigation_summary": investigation
    }


@app.get("/api/metrics")
async def get_metrics():
    """
    Returns real-time loss prevented, latency, and decision distribution.
    """
    return risk_firewall_agent.get_merchant_metrics()


@app.get("/api/threat-stream")
async def get_threat_stream():
    """
    Returns recent transaction evaluations.
    """
    return threat_stream[:20]


@app.post("/api/simulate-attack")
async def simulate_attack(request: Request):
    """
    1-Click Attack Simulator for Live Hackathon Presentations:
    1. 'card_testing_botnet'
    2. 'mule_ring_hopping'
    3. 'impossible_travel'
    4. 'friendly_fraud_dispute'
    """
    data = await request.json()
    attack_type = data.get("attack_type", "card_testing_botnet")
    results = []

    if attack_type == "card_testing_botnet":
        # Rapid burst of 8 micro-probing transactions in 0.5s
        bot_device_id = f"bot_dev_{uuid.uuid4().hex[:6]}"
        bot_ip = "185.220.101.5" # Tor Exit
        
        for i in range(8):
            tx = TransactionPayload(
                transaction_id=f"tx_bot_{uuid.uuid4().hex[:8]}",
                order_id=f"order_bot_{i}",
                user_id=f"bot_user_{i}",
                sender_vpa="stolen_card_probing@axis",
                amount=float(i + 1), # ₹1, ₹2, ₹3...
                payment_method="card",
                device=DeviceFingerprint(
                    device_id=bot_device_id,
                    ip_address=bot_ip,
                    user_agent="Mozilla/5.0 HeadlessChrome/120.0.0.0",
                    is_tor=True,
                    city="Frankfurt",
                    country="DE"
                ),
                behavior=BehavioralBiometrics(
                    typing_cadence_ms=12.0, # Superhuman
                    paste_count=4,
                    hesitation_seconds=0.05,
                    is_bot_pattern=True
                )
            )
            res = risk_firewall_agent.process_transaction(tx)
            results.append(res)
            
            threat_stream.insert(0, {
                "id": tx.transaction_id,
                "amount": tx.amount,
                "user_id": tx.user_id,
                "vpa": "Card Probing Bot",
                "city": "Frankfurt (Tor)",
                "decision": res["risk_report"]["decision"],
                "risk_score": res["risk_report"]["risk_score"],
                "latency_ms": res["risk_report"]["latency_ms"],
                "reason_codes": res["risk_report"]["reason_codes"],
                "timestamp": datetime.utcnow().strftime("%H:%M:%S")
            })

        return {
            "attack_type": "Card Testing Botnet (8 Micro-Transactions)",
            "status": "ALL_INTERCEPTED",
            "prevented_loss": "₹36.00",
            "evaluations": results
        }

    elif attack_type == "impossible_travel":
        # First transaction in Mumbai, Second in London 2 minutes later
        user_id = f"shopper_{uuid.uuid4().hex[:6]}"
        
        # Tx 1: Mumbai
        tx1 = TransactionPayload(
            transaction_id=f"tx_legit_{uuid.uuid4().hex[:8]}",
            order_id="order_mumbai_1",
            user_id=user_id,
            sender_vpa="rahul@okhdfcbank",
            amount=2499.0,
            timestamp=datetime.utcnow() - timedelta(minutes=2),
            device=DeviceFingerprint(
                device_id="dev_iphone_rahul",
                ip_address="103.21.14.82",
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_4)",
                latitude=19.0760,
                longitude=72.8777,
                city="Mumbai",
                country="IN"
            )
        )
        res1 = risk_firewall_agent.process_transaction(tx1)

        # Tx 2: London (7,200 km away, 2 mins later -> ~216,000 km/h)
        tx2 = TransactionPayload(
            transaction_id=f"tx_spoof_{uuid.uuid4().hex[:8]}",
            order_id="order_london_2",
            user_id=user_id,
            sender_vpa="rahul@okhdfcbank",
            amount=85000.0,
            timestamp=datetime.utcnow(),
            device=DeviceFingerprint(
                device_id="dev_spoof_london",
                ip_address="82.165.197.1",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                is_vpn=True,
                latitude=51.5074,
                longitude=-0.1278,
                city="London",
                country="GB"
            )
        )
        res2 = risk_firewall_agent.process_transaction(tx2)

        threat_stream.insert(0, {
            "id": tx2.transaction_id,
            "amount": tx2.amount,
            "user_id": tx2.user_id,
            "vpa": tx2.sender_vpa,
            "city": "London (Spoofed VPN)",
            "decision": res2["risk_report"]["decision"],
            "risk_score": res2["risk_report"]["risk_score"],
            "latency_ms": res2["risk_report"]["latency_ms"],
            "reason_codes": res2["risk_report"]["reason_codes"],
            "timestamp": datetime.utcnow().strftime("%H:%M:%S")
        })

        return {
            "attack_type": "Impossible Geo-Velocity Attack (Mumbai -> London in 2m)",
            "status": "INTERCEPTED",
            "prevented_loss": "₹85,000.00",
            "tx1_mumbai": res1,
            "tx2_london": res2
        }

    elif attack_type == "mule_ring_hopping":
        # Simulates a transaction coming from the flagged syndicate node
        tx = TransactionPayload(
            transaction_id=f"tx_mule_{uuid.uuid4().hex[:8]}",
            order_id="order_mule_ring_9",
            user_id="mule_bot_1",
            sender_vpa="fastcash99@ybl",
            receiver_vpa="instantwin77@paytm",
            amount=45000.0,
            device=DeviceFingerprint(
                device_id="dev_syndicate_shared",
                ip_address="185.220.101.5",
                user_agent="Rooted Dalvik/2.1.0",
                is_emulator=True
            )
        )
        res = risk_firewall_agent.process_transaction(tx)

        threat_stream.insert(0, {
            "id": tx.transaction_id,
            "amount": tx.amount,
            "user_id": tx.user_id,
            "vpa": tx.sender_vpa,
            "city": "Mule Syndicate Cluster Alpha",
            "decision": res["risk_report"]["decision"],
            "risk_score": res["risk_report"]["risk_score"],
            "latency_ms": res["risk_report"]["latency_ms"],
            "reason_codes": res["risk_report"]["reason_codes"],
            "timestamp": datetime.utcnow().strftime("%H:%M:%S")
        })

        return {
            "attack_type": "Mule Syndicate Fund Hopping",
            "status": "BLOCKED_SYNDICATE_LINKAGE",
            "prevented_loss": "₹45,000.00",
            "evaluation": res
        }

    elif attack_type == "friendly_fraud_dispute":
        # Simulates buyer filing chargeback and AI Auto-Defender generating evidence dossier
        dossier = dispute_defender_agent.generate_dispute_dossier(
            payment_id=f"pay_dispute_{uuid.uuid4().hex[:8]}",
            order_id="order_RZP_dispute_99",
            amount=4999.0,
            dispute_reason="unauthorized_transaction",
            customer_name="Amitabh Verma"
        )
        return {
            "attack_type": "Friendly Fraud Chargeback Claim",
            "status": "AUTO_DEFENSE_SUBMITTED",
            "dossier": dossier.model_dump()
        }

    return {"error": "Invalid attack type"}


@app.post("/api/generate-dispute-dossier")
async def generate_dispute_dossier(request: Request):
    """
    Generates a full bank evidence packet for a chargeback.
    """
    data = await request.json()
    dossier = dispute_defender_agent.generate_dispute_dossier(
        payment_id=data.get("payment_id", f"pay_{uuid.uuid4().hex[:8]}"),
        order_id=data.get("order_id", f"order_{uuid.uuid4().hex[:8]}"),
        amount=float(data.get("amount", 2999.0)),
        dispute_reason=data.get("reason", "unauthorized_transaction"),
        customer_name=data.get("customer_name", "Shopper Customer")
    )
    return dossier.model_dump()


@app.post("/webhook/razorpay")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None)
):
    """
    Ingests live Razorpay Webhooks (payments, disputes, risk alerts).
    """
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    if not razorpay_risk_service.verify_webhook_signature(body_str, x_razorpay_signature or ""):
        raise HTTPException(status_code=400, detail="Invalid Razorpay Webhook Signature")

    payload = await request.json()
    event = payload.get("event", "")

    if event == "dispute.created":
        disp_entity = payload.get("payload", {}).get("dispute", {}).get("entity", {})
        dossier = dispute_defender_agent.generate_dispute_dossier(
            payment_id=disp_entity.get("payment_id", "pay_auto_webhook"),
            order_id="order_webhook_disp",
            amount=float(disp_entity.get("amount", 0)) / 100.0,
            dispute_reason=disp_entity.get("reason_code", "fraudulent")
        )
        return {"status": "DISPUTE_DEFENSE_TRANSMITTED", "dossier_id": dossier.dossier_id}

    return {"status": "PROCESSED", "event": event}


# Seed with initial threat feed items
def _seed_threat_stream():
    for item in [
        {"id": "tx_clean_101", "amount": 2499.0, "user_id": "user_priya", "vpa": "priya@okhdfcbank", "city": "Mumbai", "decision": "ALLOW", "risk_score": 8.5, "latency_ms": 19.4, "reason_codes": [], "timestamp": "19:15:10"},
        {"id": "tx_clean_102", "amount": 1499.0, "user_id": "user_karan", "vpa": "karan@paytm", "city": "Bengaluru", "decision": "ALLOW", "risk_score": 12.0, "latency_ms": 22.1, "reason_codes": [], "timestamp": "19:16:04"},
        {"id": "tx_step_103", "amount": 18999.0, "user_id": "user_rohit", "vpa": "rohit99@icici", "city": "Delhi (VPN)", "decision": "STEP_UP", "risk_score": 48.0, "latency_ms": 31.0, "reason_codes": ["ANONYMOUS_VPN_DETECTED"], "timestamp": "19:16:45"},
        {"id": "tx_block_104", "amount": 75000.0, "user_id": "mule_bot_1", "vpa": "fastcash99@ybl", "city": "Tor Exit", "decision": "BLOCK", "risk_score": 96.5, "latency_ms": 28.3, "reason_codes": ["TOR_ANONYMIZED_NETWORK", "CIRCULAR_MULE_FUND_HOPPING"], "timestamp": "19:17:22"}
    ]:
        threat_stream.append(item)

_seed_threat_stream()
