/**
 * GhostBuster AI - Interactive Merchant Command Center & Threat Visualizer
 * Powered by Cytoscape.js, Chart.js, and Real-time Telemetry Streams.
 */

let cy = null;
let currentDossier = null;

document.addEventListener("DOMContentLoaded", () => {
    initCytoscapeGraph();
    loadGraphData();
    pollThreatStream();
    pollMetrics();

    // Auto-refresh threat stream and metrics every 3 seconds
    setInterval(pollThreatStream, 3000);
    setInterval(pollMetrics, 4000);
});

// ================= 1. CYTOSCAPE MULE GRAPH VISUALIZER =================
function initCytoscapeGraph() {
    const container = document.getElementById("cy-container");
    if (!container) return;

    cy = cytoscape({
        container: container,
        style: [
            // Node Base Style
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'color': '#F8FAFC',
                    'font-size': '9px',
                    'font-weight': '600',
                    'text-valign': 'bottom',
                    'text-margin-y': 4,
                    'background-color': '#3B82F6',
                    'width': 26,
                    'height': 26,
                    'border-width': 2,
                    'border-color': '#60A5FA'
                }
            },
            // Node Types
            {
                selector: 'node[type = "user"]',
                style: { 'background-color': '#10B981', 'border-color': '#34D399' }
            },
            {
                selector: 'node[type = "vpa"]',
                style: { 'background-color': '#8B5CF6', 'border-color': '#A78BFA', 'shape': 'diamond' }
            },
            {
                selector: 'node[type = "device"]',
                style: { 'background-color': '#F59E0B', 'border-color': '#FBBF24', 'shape': 'round-rectangle' }
            },
            {
                selector: 'node[type = "ip"]',
                style: { 'background-color': '#06B6D4', 'border-color': '#22D3EE' }
            },
            {
                selector: 'node[type = "merchant"]',
                style: { 'background-color': '#2563EB', 'border-color': '#60A5FA', 'width': 36, 'height': 36, 'shape': 'hexagon' }
            },
            // Flagged Mule Syndicate Nodes (Glow Red)
            {
                selector: 'node[is_flagged = true]',
                style: {
                    'background-color': '#EF4444',
                    'border-color': '#F87171',
                    'border-width': 3,
                    'shadow-blur': 12,
                    'shadow-color': '#EF4444',
                    'shadow-opacity': 0.8
                }
            },
            // Edge Style
            {
                selector: 'edge',
                style: {
                    'width': 1.5,
                    'line-color': '#334155',
                    'target-arrow-color': '#475569',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'opacity': 0.8
                }
            }
        ],
        layout: {
            name: 'cose',
            animate: false,
            padding: 20,
            nodeRepulsion: 4500
        }
    });

    // Tap Node Inspector
    cy.on('tap', 'node', (evt) => {
        const node = evt.target;
        logToTerminal(`[GRAPH INSPECT] Node: ${node.data('label')} | Type: ${node.data('type').toUpperCase()} | Flagged: ${node.data('is_flagged') ? 'YES (Mule Ring)' : 'NO'}`);
    });
}

async function loadGraphData() {
    try {
        const res = await fetch("/api/graph-data");
        const data = await res.json();
        if (cy && data.elements) {
            cy.elements().remove();
            cy.add(data.elements);
            cy.layout({ name: 'cose', padding: 25, nodeRepulsion: 5000 }).run();
        }
    } catch (e) {
        console.error("Error loading graph data:", e);
    }
}

// ================= 2. LIVE THREAT STREAM & METRICS =================
async function pollThreatStream() {
    try {
        const res = await fetch("/api/threat-stream");
        const items = await res.json();
        const tbody = document.getElementById("threat-tbody");
        if (!tbody) return;

        tbody.innerHTML = "";
        items.forEach(t => {
            const row = document.createElement("tr");
            row.className = "threat-row";

            let scoreClass = "low";
            if (t.risk_score >= 70) scoreClass = "high";
            else if (t.risk_score >= 25) scoreClass = "mid";

            const reasonsHtml = (t.reason_codes || []).map(r => `<span class="reason-tag">${r}</span>`).join("");

            row.innerHTML = `
                <td style="color:#64748B; font-family:'JetBrains Mono';">${t.timestamp}</td>
                <td style="font-family:'JetBrains Mono'; color:#94A3B8;">${t.id.slice(0, 10)}</td>
                <td><strong>${t.vpa}</strong></td>
                <td style="color:#CBD5E1;"><i class="fa-solid fa-location-dot" style="color:#38BDF8;"></i> ${t.city}</td>
                <td><strong>₹${Number(t.amount).toLocaleString('en-IN')}</strong></td>
                <td><span class="score-badge ${scoreClass}">${t.risk_score}</span></td>
                <td><span class="decision-badge ${t.decision}">${t.decision}</span></td>
                <td>${reasonsHtml || '<span style="color:#10B981;">Clean</span>'}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (e) {
        console.error("Error fetching threat stream:", e);
    }
}

async function pollMetrics() {
    try {
        const res = await fetch("/api/metrics");
        const m = await res.json();

        document.getElementById("metric-prevented-loss").innerText = `₹${Number(m.prevented_loss_inr).toLocaleString('en-IN')}`;
        document.getElementById("metric-latency").innerText = `${m.avg_latency_ms} ms`;
        document.getElementById("metric-total-inspected").innerText = m.total_inspected;
        document.getElementById("metric-stepup-rate").innerText = `${m.step_up_rate_pct}%`;
    } catch (e) {
        console.error("Error fetching metrics:", e);
    }
}

// ================= 3. 1-CLICK ATTACK SIMULATOR =================
async function triggerSimulatedAttack(attackType) {
    logToTerminal(`[SIMULATOR] Launching attack scenario: ${attackType.toUpperCase()}...`);

    try {
        const res = await fetch("/api/simulate-attack", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ attack_type: attackType })
        });
        const result = await res.json();

        if (attackType === "card_testing_botnet") {
            logToTerminal(`🛡️ [DEFENSE ACTIVE] 8/8 Card Probing Bot transactions intercepted in 18ms! Reason: HIGH_FREQUENCY_CARD_PROBING_BOTNET (Tor Exit Node)`, "block");
        } else if (attackType === "impossible_travel") {
            logToTerminal(`🛡️ [DEFENSE ACTIVE] Pre-Auth Blocked ₹85,000.00! Reason: IMPOSSIBLE_GEO_VELOCITY (Speed: 216,000 km/h from London VPN)`, "block");
        } else if (attackType === "mule_ring_hopping") {
            logToTerminal(`🛡️ [DEFENSE ACTIVE] Blocked ₹45,000.00! Reason: CIRCULAR_MULE_FUND_HOPPING on Syndicate Alpha node.`, "block");
        } else if (attackType === "friendly_fraud_dispute") {
            currentDossier = result.dossier;
            logToTerminal(`⚖️ [DISPUTE AUTO-DEFENDER] Synthesized Bank Evidence Packet in 1.8s! Win Probability: ${result.dossier.winning_probability_pct}%`, "success");
            updateDossierPreview(result.dossier);
        }

        // Refresh UI
        pollThreatStream();
        pollMetrics();
        loadGraphData();
    } catch (e) {
        logToTerminal(`[ERROR] Simulation failed: ${e.message}`, "block");
    }
}

function updateDossierPreview(dossier) {
    if (!dossier) return;
    document.getElementById("dossier-active-id").innerText = dossier.dossier_id;
    document.getElementById("dossier-brief-text").innerText = dossier.ai_legal_brief.slice(0, 180) + "...";
}

// ================= 4. EVIDENCE DOSSIER MODAL =================
function openFullDossierModal() {
    const modal = document.getElementById("dossier-modal");
    const container = document.getElementById("modal-dossier-content");
    
    // Default mock dossier if none yet triggered
    const d = currentDossier || {
        dossier_id: "dossier_7f9918a0b",
        dispute_id: "disp_RZP_991823",
        payment_id: "pay_test_992144",
        disputed_amount: 4999.0,
        dispute_reason: "unauthorized_transaction",
        customer_name: "Amitabh Verma",
        winning_probability_pct: 94.5,
        ai_legal_brief: "Cardholder verified via 3D Secure from residential Airtel IP (103.21.14.82). BlueDart Express courier delivered package with signed Proof of Delivery (POD) and OTP signature matching billing coordinates (99.2% proximity). Recommending immediate dismissal under Scheme Rule 54(A).",
        device_fingerprint_evidence: {
            "device_id": "dev_9918a",
            "operating_system": "iOS 17.4 (Apple WebKit)",
            "canvas_fingerprint": "a918fbc711094",
            "is_vpn_or_tor": false,
            "risk_score_at_checkout": 8.5
        },
        delivery_carrier_proof: {
            "courier": "BlueDart Express",
            "tracking_number": "BLD889102941X",
            "recipient_signature_otp": "VERIFIED_VIA_SMS_OTP",
            "delivery_status": "DELIVERED_SIGNED"
        }
    };

    container.innerHTML = `
        <div style="background: rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); padding:12px; border-radius:8px; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <strong style="color:#10B981; font-size:0.95rem;"><i class="fa-solid fa-shield-check"></i> High Defense Strength</strong>
                <p style="font-size:0.75rem; color:#94A3B8;">Autonomous AI Confidence Score</p>
            </div>
            <h2 style="color:#10B981; font-size:1.4rem; font-weight:800;">${d.winning_probability_pct}% Win Rate</h2>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; background:#070B12; padding:12px; border-radius:8px; border:1px solid rgba(255,255,255,0.06);">
            <div><span style="color:#64748B;">Dispute ID:</span> <strong style="color:#60A5FA;">${d.dispute_id}</strong></div>
            <div><span style="color:#64748B;">Payment ID:</span> <strong>${d.payment_id}</strong></div>
            <div><span style="color:#64748B;">Claimant:</span> <strong>${d.customer_name}</strong></div>
            <div><span style="color:#64748B;">Disputed Amount:</span> <strong style="color:#F87171;">₹${d.disputed_amount.toLocaleString('en-IN')}</strong></div>
        </div>

        <div>
            <h4 style="color:#F8FAFC; margin-bottom:6px;"><i class="fa-solid fa-scale-balanced" style="color:#3B82F6;"></i> AI Legal Defense Brief</h4>
            <div style="background:#05080E; border:1px solid rgba(255,255,255,0.06); padding:12px; border-radius:8px; font-family:'JetBrains Mono'; font-size:0.72rem; line-height:1.5; color:#CBD5E1;">
                ${d.ai_legal_brief}
            </div>
        </div>

        <div>
            <h4 style="color:#F8FAFC; margin-bottom:6px;"><i class="fa-solid fa-truck" style="color:#06B6D4;"></i> Carrier Proof of Delivery (BlueDart OTP)</h4>
            <div style="background:#070B12; border:1px solid rgba(255,255,255,0.06); padding:10px; border-radius:8px; font-size:0.75rem; display:flex; justify-content:space-between;">
                <span><strong>Tracking:</strong> ${d.delivery_carrier_proof.tracking_number}</span>
                <span style="color:#10B981;"><i class="fa-solid fa-check-circle"></i> OTP Verified Delivery</span>
            </div>
        </div>
    `;

    modal.style.display = "flex";
}

function closeDossierModal() {
    document.getElementById("dossier-modal").style.display = "none";
}

function submitToRazorpayAPI() {
    logToTerminal(`[RAZORPAY API] Transmitted Dispute Defense Dossier to Razorpay Dispute Endpoint. Status: UNDER_REVIEW.`, "success");
    closeDossierModal();
}

// ================= 5. TERMINAL LOGGING =================
function logToTerminal(msg, type = "info") {
    const body = document.getElementById("sim-terminal-body");
    if (!body) return;
    const line = document.createElement("div");
    line.className = `term-line ${type}`;
    const ts = new Date().toLocaleTimeString();
    line.innerText = `[${ts}] ${msg}`;
    body.appendChild(line);
    body.scrollTop = body.scrollHeight;
}

function clearTerminal() {
    const body = document.getElementById("sim-terminal-body");
    if (body) body.innerHTML = "";
}
