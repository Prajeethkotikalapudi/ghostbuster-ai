/**
 * GhostBuster.AI - Live Animated Application Presentation Controller
 * Orchestrates virtual cursor movement, live simulated clicks, dynamic graph rendering,
 * terminal streaming, and synchronized AI voice narration with zero dead gaps.
 */

let cyMock = null;
let currentSceneIndex = 0;
let isPlaying = false;
let isMuted = false;
let playbackSpeed = 1.0;
let sceneTimer = null;
let currentElapsedSeconds = 0;
let synth = window.speechSynthesis;
let currentUtterance = null;

// Estimated scene durations for timeline bar (~240s total)
const SCENE_DURATIONS = [35, 45, 40, 45, 45, 30];
const totalDurationSeconds = SCENE_DURATIONS.reduce((a, b) => a + b, 0);

// Video recorder
let mediaRecorder = null;
let recordedChunks = [];
let isRecording = false;

// ================= DYNAMIC GRAPH TOPOLOGY STATES =================
const GRAPH_STATES = {
    baseline: {
        bannerText: "Live Network Baseline: Verified Shoppers & Authenticated VPAs",
        bannerClass: "normal",
        elements: [
            { data: { id: 'u_priya', label: 'Priya S. (Verified)', type: 'user' } },
            { data: { id: 'v_priya', label: 'priya@okhdfc', type: 'vpa' } },
            { data: { id: 'd_priya', label: 'iPhone 15 Pro', type: 'device' } },
            { data: { id: 'ip_priya', label: '103.21.14.82 (Mumbai)', type: 'ip' } },
            { data: { id: 'm_rzp', label: 'Razorpay Merchant', type: 'merchant' } },
            { data: { id: 'u_karan', label: 'Karan M.', type: 'user' } },
            { data: { id: 'v_karan', label: 'karan@paytm', type: 'vpa' } },

            { data: { source: 'u_priya', target: 'v_priya' } },
            { data: { source: 'u_priya', target: 'd_priya' } },
            { data: { source: 'd_priya', target: 'ip_priya' } },
            { data: { source: 'v_priya', target: 'm_rzp' } },
            { data: { source: 'u_karan', target: 'v_karan' } },
            { data: { source: 'v_karan', target: 'm_rzp' } }
        ]
    },
    botnet: {
        bannerText: "🚨 Attack Ingested: Tor Exit Node Botnet Probing Blocked (8 Nodes)",
        bannerClass: "critical",
        elements: [
            { data: { id: 'tor_master', label: 'Tor Exit 185.220.101.5', type: 'ip', is_flagged: true } },
            { data: { id: 'bot_runner', label: 'HeadlessChrome Bot', type: 'device', is_flagged: true } },
            { data: { id: 'card_p1', label: 'Probing Card #1 (₹1)', type: 'vpa', is_flagged: true } },
            { data: { id: 'card_p2', label: 'Probing Card #2 (₹2)', type: 'vpa', is_flagged: true } },
            { data: { id: 'card_p3', label: 'Probing Card #3 (₹3)', type: 'vpa', is_flagged: true } },
            { data: { id: 'card_p4', label: 'Probing Card #4 (₹4)', type: 'vpa', is_flagged: true } },
            { data: { id: 'm_rzp', label: 'Razorpay Merchant (Shielded)', type: 'merchant' } },

            { data: { source: 'tor_master', target: 'bot_runner' } },
            { data: { source: 'bot_runner', target: 'card_p1' } },
            { data: { source: 'bot_runner', target: 'card_p2' } },
            { data: { source: 'bot_runner', target: 'card_p3' } },
            { data: { source: 'bot_runner', target: 'card_p4' } },
            { data: { id: 'b_edge1', source: 'card_p1', target: 'm_rzp' }, classes: 'active-cycle' },
            { data: { id: 'b_edge2', source: 'card_p2', target: 'm_rzp' }, classes: 'active-cycle' },
            { data: { id: 'b_edge3', source: 'card_p3', target: 'm_rzp' }, classes: 'active-cycle' },
            { data: { id: 'b_edge4', source: 'card_p4', target: 'm_rzp' }, classes: 'active-cycle' }
        ]
    },
    travel: {
        bannerText: "🚨 Impossible Travel: Mumbai (19.07) -> London (51.50) in 2m (216,000 km/h)",
        bannerClass: "critical",
        elements: [
            { data: { id: 'u_rahul', label: 'Rahul S. (Compromised)', type: 'user', is_flagged: true } },
            { data: { id: 'd_mumbai', label: 'Mumbai iPhone (19:14)', type: 'device' } },
            { data: { id: 'ip_mumbai', label: '103.21.14.82 (Mumbai)', type: 'ip' } },
            { data: { id: 'd_london', label: 'London VPN (19:16)', type: 'device', is_flagged: true } },
            { data: { id: 'ip_london', label: '82.165.197.1 (London)', type: 'ip', is_flagged: true } },
            { data: { id: 'm_rzp', label: 'Razorpay Target (₹85,000)', type: 'merchant' } },

            { data: { source: 'u_rahul', target: 'd_mumbai' } },
            { data: { source: 'd_mumbai', target: 'ip_mumbai' } },
            { data: { id: 'imp_hop', source: 'u_rahul', target: 'd_london' }, classes: 'active-cycle' },
            { data: { source: 'd_london', target: 'ip_london' } },
            { data: { id: 'b_travel', source: 'd_london', target: 'm_rzp' }, classes: 'active-cycle' }
        ]
    },
    mule_ring: {
        bannerText: "🚨 Active Syndicate Ring: SYNDICATE_ALPHA (3 VPAs • Circular Flow • 1 Shared Emulator)",
        bannerClass: "critical",
        elements: [
            { data: { id: 'mule_1', label: 'Mule #1 (fastcash99)', type: 'user', is_flagged: true } },
            { data: { id: 'vpa_m1', label: 'fastcash99@ybl', type: 'vpa', is_flagged: true } },
            { data: { id: 'mule_2', label: 'Mule #2 (instantwin77)', type: 'user', is_flagged: true } },
            { data: { id: 'vpa_m2', label: 'instantwin77@paytm', type: 'vpa', is_flagged: true } },
            { data: { id: 'mule_3', label: 'Mule #3 (darknode33)', type: 'user', is_flagged: true } },
            { data: { id: 'vpa_m3', label: 'darknode33@axis', type: 'vpa', is_flagged: true } },
            { data: { id: 'd_emu', label: 'Rooted Dalvik Emulator', type: 'device', is_flagged: true } },

            { data: { source: 'mule_1', target: 'vpa_m1' } },
            { data: { source: 'mule_2', target: 'vpa_m2' } },
            { data: { source: 'mule_3', target: 'vpa_m3' } },
            { data: { source: 'mule_1', target: 'd_emu' } },
            { data: { source: 'mule_2', target: 'd_emu' } },
            { data: { source: 'mule_3', target: 'd_emu' } },
            { data: { id: 'cycle1', source: 'vpa_m1', target: 'vpa_m2' }, classes: 'active-cycle' },
            { data: { id: 'cycle2', source: 'vpa_m2', target: 'vpa_m3' }, classes: 'active-cycle' },
            { data: { id: 'cycle3', source: 'vpa_m3', target: 'vpa_m1' }, classes: 'active-cycle' }
        ]
    },
    dispute: {
        bannerText: "⚖️ Dispute Evidence Graph: 3D Secure + Residential IP (99.2% proximity) + BlueDart OTP",
        bannerClass: "verified",
        elements: [
            { data: { id: 'c_amitabh', label: 'Amitabh Verma (Cardholder)', type: 'user' } },
            { data: { id: 'auth_2fa', label: '3D Secure / MPIN Verified', type: 'vpa' } },
            { data: { id: 'ip_home', label: 'Airtel Residential IP (103.21)', type: 'ip' } },
            { data: { id: 'courier_pod', label: 'BlueDart Signed OTP (POD)', type: 'device' } },
            { data: { id: 'rzp_disp', label: 'Razorpay Dispute API', type: 'merchant' } },

            { data: { source: 'c_amitabh', target: 'auth_2fa' } },
            { data: { source: 'auth_2fa', target: 'ip_home' } },
            { data: { source: 'c_amitabh', target: 'courier_pod' } },
            { data: { source: 'courier_pod', target: 'rzp_disp' } },
            { data: { source: 'auth_2fa', target: 'rzp_disp' } }
        ]
    }
};

const WALKTHROUGH_SCENES = [
    {
        id: 0,
        title: "Command Center & Metrics Overview",
        caption: "GhostBuster.AI: Live Merchant Command Center with sub-30ms SLA and real-time loss prevention.",
        narration: "Welcome to GhostBuster AI. Here is our live Merchant Command Center. Unlike legacy rule engines that process transactions after the fact, GhostBuster AI operates at the pre-authorization layer in under thirty milliseconds. Notice our real-time metrics: over one point six six lakh rupees in direct fraud loss prevented, an average inspection latency of twenty-four point five milliseconds, and a ninety-four point eight percent step-up conversion rate ensuring zero legitimate customer drop-off.",
        action: () => {
            resetUI();
            setGraphState('baseline');
            moveCursor(16, 25);
            highlightElement("mockup-metrics");
        }
    },
    {
        id: 1,
        title: "Live Simulation: Card Testing Botnet",
        caption: "Simulating Card Testing Botnet: 8 micro-probing authorizations intercepted over Tor in 18ms.",
        narration: "Now, watch what happens when a card-testing botnet launches an automated attack, cycling stolen card credentials with rapid micro-authorizations under ten rupees. Our virtual cursor clicks the Card Testing Botnet simulator. In just eighteen milliseconds, GhostBuster AI detects the Tor exit node, the superhuman twelve millisecond keystroke cadence, and intercepts all eight transactions before card authorization, protecting the merchant from costly card network fines.",
        action: () => {
            resetUI();
            setGraphState('botnet');
            moveCursor(38, 18, () => {
                triggerClickEffect("btn-mock-botnet");
                simulateBotnetLogs();
            });
        }
    },
    {
        id: 2,
        title: "Live Simulation: Impossible Geo-Velocity",
        caption: "Simulating Impossible Geo-Velocity: Mumbai to London in 2m (216,000 km/h) blocked before authorization.",
        narration: "Next, an attacker in London attempts an account takeover on a shopper who transacted in Mumbai just two minutes ago. We click Impossible Geo-Velocity. The Haversine trigonometric physics engine calculates that traveling seven thousand two hundred kilometers in two minutes requires a speed of two hundred sixteen thousand kilometers per hour. GhostBuster AI flags impossible travel and blocks the eighty-five thousand rupee transaction instantly.",
        action: () => {
            resetUI();
            setGraphState('travel');
            moveCursor(38, 38, () => {
                triggerClickEffect("btn-mock-travel");
                simulateTravelLogs();
            });
        }
    },
    {
        id: 3,
        title: "Real-Time Mule Syndicate Graph Traversal",
        caption: "Cytoscape Mule Network Graph: Traverses 2-hop circular fund-hopping across pooled emulators in real-time.",
        narration: "On the right panel is our real-time Cytoscape Mule Network Graph. Financial cybercriminals attempt to bypass static single-account limits by hopping funds through circular rings of dormant mule accounts and pooled mobile emulators. GhostBuster AI dynamically traverses graph adjacency, detecting circular cycles and shared hardware fingerprints to dismantle entire fraud syndicates like Syndicate Alpha.",
        action: () => {
            resetUI();
            setGraphState('mule_ring');
            moveCursor(42, 70, () => {
                highlightElement("mock-graph-panel");
                animateGraphNodes();
            });
        }
    },
    {
        id: 4,
        title: "Dispute Auto-Defender: Bank Evidence Dossier",
        caption: "Dispute Auto-Defender: Generates complete Bank Evidence Dossier with BlueDart OTP tracking in < 2s.",
        narration: "When a customer falsely claims an unauthorized purchase, our Dispute Auto-Defender Agent compiles this complete Bank Evidence Dossier in under two seconds. It bundles cardholder 3D Secure logs, residential IP coordinates with ninety-nine point two percent proximity, BlueDart carrier OTP delivery proof, and an AI legal brief under Scheme Rule 54-A with a ninety-four point five percent winning probability, eliminating manual dispute paperwork.",
        action: () => {
            resetUI();
            setGraphState('dispute');
            moveCursor(48, 38, () => {
                triggerClickEffect("btn-mock-dispute");
                openMockDossier();
            });
        }
    },
    {
        id: 5,
        title: "Razorpay Native Integration & Growth Impact",
        caption: "Native Razorpay Integration: Zero-friction pre-auth protection and 90% dispute recovery.",
        narration: "GhostBuster AI integrates natively with Razorpay Orders, Payments, and Webhook APIs with zero infrastructure friction. It turns risk management from a painful cost center into an invisible, revenue-protecting growth engine for every merchant on Razorpay. Thank you, and we invite you to explore the live interactive command center.",
        action: () => {
            resetUI();
            setGraphState('baseline');
            closeMockDossier();
            moveCursor(8, 85);
            highlightElement("mock-mockup-frame");
        }
    }
];

document.addEventListener("DOMContentLoaded", () => {
    initMockCytoscape();
    seedMockTable();
    bindInteractiveButtons();
    updateSceneView();
    updateTimeDisplay();
});

// ================= DYNAMIC GRAPH CONTROLLER =================
function initMockCytoscape() {
    const container = document.getElementById("mock-cy-container");
    if (!container) return;

    cyMock = cytoscape({
        container: container,
        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'color': '#F8FAFC',
                    'font-size': '8px',
                    'font-weight': '600',
                    'text-valign': 'bottom',
                    'text-margin-y': 3,
                    'background-color': '#3B82F6',
                    'width': 22,
                    'height': 22,
                    'border-width': 1.5,
                    'border-color': '#60A5FA',
                    'transition-property': 'background-color, border-color, width, height',
                    'transition-duration': '0.4s'
                }
            },
            { selector: 'node[type = "user"]', style: { 'background-color': '#10B981', 'border-color': '#34D399' } },
            { selector: 'node[type = "vpa"]', style: { 'background-color': '#8B5CF6', 'border-color': '#A78BFA', 'shape': 'diamond' } },
            { selector: 'node[type = "device"]', style: { 'background-color': '#F59E0B', 'border-color': '#FBBF24', 'shape': 'round-rectangle' } },
            { selector: 'node[type = "ip"]', style: { 'background-color': '#06B6D4', 'border-color': '#22D3EE' } },
            { selector: 'node[type = "merchant"]', style: { 'background-color': '#2563EB', 'border-color': '#60A5FA', 'width': 28, 'height': 28, 'shape': 'hexagon' } },
            {
                selector: 'node[is_flagged = true]',
                style: {
                    'background-color': '#EF4444',
                    'border-color': '#F87171',
                    'border-width': 3,
                    'shadow-blur': 12,
                    'shadow-color': '#EF4444',
                    'shadow-opacity': 0.9
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 1.4,
                    'line-color': '#334155',
                    'target-arrow-color': '#475569',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'opacity': 0.8
                }
            },
            {
                selector: 'edge.active-cycle',
                style: {
                    'line-color': '#EF4444',
                    'target-arrow-color': '#EF4444',
                    'width': 2.5,
                    'opacity': 1.0,
                    'line-style': 'dashed'
                }
            }
        ],
        elements: GRAPH_STATES.baseline.elements,
        layout: { name: 'cose', animate: false, padding: 15, nodeRepulsion: 3500 }
    });
}

function setGraphState(stateKey) {
    if (!cyMock || !GRAPH_STATES[stateKey]) return;

    const state = GRAPH_STATES[stateKey];
    
    // Update Banner
    const banner = document.getElementById("mock-syn-banner");
    if (banner) {
        banner.innerHTML = `<i class="fa-solid fa-circle-nodes"></i> <span>${state.bannerText}</span>`;
        if (state.bannerClass === 'verified') {
            banner.style.background = "rgba(16, 185, 129, 0.12)";
            banner.style.borderColor = "rgba(16, 185, 129, 0.35)";
            banner.style.color = "#34D399";
        } else if (state.bannerClass === 'critical') {
            banner.style.background = "rgba(239, 68, 68, 0.15)";
            banner.style.borderColor = "rgba(239, 68, 68, 0.4)";
            banner.style.color = "#F87171";
        } else {
            banner.style.background = "rgba(59, 130, 246, 0.1)";
            banner.style.borderColor = "rgba(59, 130, 246, 0.25)";
            banner.style.color = "#93C5FD";
        }
    }

    // Morph elements smoothly
    cyMock.elements().remove();
    cyMock.add(state.elements);
    cyMock.layout({
        name: 'cose',
        animate: true,
        animationDuration: 400,
        padding: 15,
        nodeRepulsion: 4000
    }).run();
}

function animateGraphNodes() {
    if (!cyMock) return;
    const synNodes = cyMock.nodes('[is_flagged = true]');
    synNodes.flashClass('highlighted', 2000);
}

// Bind interactive user clicks on simulator buttons in the video
function bindInteractiveButtons() {
    const btnBotnet = document.getElementById("btn-mock-botnet");
    const btnTravel = document.getElementById("btn-mock-travel");
    const btnMule = document.getElementById("btn-mock-mule");
    const btnDispute = document.getElementById("btn-mock-dispute");

    if (btnBotnet) {
        btnBotnet.onclick = () => {
            currentSceneIndex = 1;
            updateSceneView();
            if (isPlaying) startScene(1);
        };
    }
    if (btnTravel) {
        btnTravel.onclick = () => {
            currentSceneIndex = 2;
            updateSceneView();
            if (isPlaying) startScene(2);
        };
    }
    if (btnMule) {
        btnMule.onclick = () => {
            currentSceneIndex = 3;
            updateSceneView();
            if (isPlaying) startScene(3);
        };
    }
    if (btnDispute) {
        btnDispute.onclick = () => {
            currentSceneIndex = 4;
            updateSceneView();
            if (isPlaying) startScene(4);
        };
    }
}

// ================= ANIMATION & CURSOR CONTROLLER =================
function moveCursor(topPercent, leftPercent, callback = null) {
    const cursor = document.getElementById("virtual-cursor");
    if (!cursor) return;

    cursor.style.top = `${topPercent}%`;
    cursor.style.left = `${leftPercent}%`;

    setTimeout(() => {
        if (callback) callback();
    }, 700);
}

function triggerClickEffect(elementId) {
    const el = document.getElementById(elementId);
    const ripple = document.getElementById("cursor-ripple");
    
    if (ripple) {
        ripple.classList.add("click-active");
        setTimeout(() => ripple.classList.remove("click-active"), 400);
    }

    if (el) {
        el.classList.add("active-click");
        setTimeout(() => el.classList.remove("active-click"), 300);
    }
}

function highlightElement(elementId) {
    document.querySelectorAll(".mock-metric-card, .mock-panel").forEach(e => e.classList.remove("highlighted"));
    const el = document.getElementById(elementId);
    if (el) el.classList.add("highlighted");
}

function resetUI() {
    document.querySelectorAll(".mock-metric-card, .mock-panel").forEach(e => e.classList.remove("highlighted"));
    closeMockDossier();
}

function openMockDossier() {
    const modal = document.getElementById("mock-dossier-modal");
    if (modal) modal.classList.add("active");
}

function closeMockDossier() {
    const modal = document.getElementById("mock-dossier-modal");
    if (modal) modal.classList.remove("active");
}

// ================= TERMINAL & TABLE STREAM SIMULATORS =================
function simulateBotnetLogs() {
    const body = document.getElementById("mock-terminal-body");
    if (!body) return;

    body.innerHTML = `
        <div class="term-row info">[ATTACK] Inbound Card-Testing Botnet detected (8 concurrent authorizations)</div>
        <div class="term-row block">🛡️ [PRE-AUTH BLOCK] 8/8 Intercepted in 18ms &bull; TOR_ANONYMIZED_NETWORK &bull; Typing Cadence: 12ms (Superhuman)</div>
        <div class="term-row success">[ESCROW] Saved ₹36.00 across stolen card pool. Reason: BOTNET_PROBING.</div>
    `;

    insertMockTableRow("tx_bot_7891", "Card Probing Bot", "Frankfurt (Tor)", "₹2.00", "96.5", "BLOCK", "TOR_ANONYMIZED_NETWORK");
}

function simulateTravelLogs() {
    const body = document.getElementById("mock-terminal-body");
    if (!body) return;

    body.innerHTML = `
        <div class="term-row info">[GEO-VELOCITY] User rahul@okhdfc requested ₹85,000 tx from London VPN</div>
        <div class="term-row block">🛡️ [PRE-AUTH BLOCK] IMPOSSIBLE_GEO_VELOCITY &bull; Distance: 7,200 km in 2m (Speed: 216,000 km/h)</div>
        <div class="term-row success">[PROTECTED] Prevented ₹85,000.00 fraudulent transfer.</div>
    `;

    document.getElementById("val-loss").innerText = "₹2,51,036";
    insertMockTableRow("tx_geo_9912", "rahul@okhdfcbank", "London (Spoofed VPN)", "₹85,000.00", "94.0", "BLOCK", "IMPOSSIBLE_GEO_VELOCITY");
}

function seedMockTable() {
    const tbody = document.getElementById("mock-table-tbody");
    if (!tbody) return;

    tbody.innerHTML = `
        <tr>
            <td style="color:#64748B;">19:15:10</td>
            <td style="font-family:'JetBrains Mono'; color:#94A3B8;">tx_clean_101</td>
            <td><strong>priya@okhdfcbank</strong></td>
            <td>Mumbai</td>
            <td><strong>₹2,499.00</strong></td>
            <td><span style="color:#10B981; font-weight:700;">8.5</span></td>
            <td><span class="mock-badge-decision ALLOW">ALLOW</span></td>
            <td style="color:#10B981;">Clean Residential IP</td>
        </tr>
        <tr>
            <td style="color:#64748B;">19:16:04</td>
            <td style="font-family:'JetBrains Mono'; color:#94A3B8;">tx_clean_102</td>
            <td><strong>karan@paytm</strong></td>
            <td>Bengaluru</td>
            <td><strong>₹1,499.00</strong></td>
            <td><span style="color:#10B981; font-weight:700;">12.0</span></td>
            <td><span class="mock-badge-decision ALLOW">ALLOW</span></td>
            <td style="color:#10B981;">Clean Residential IP</td>
        </tr>
    `;
}

function insertMockTableRow(id, vpa, loc, amt, score, decision, reason) {
    const tbody = document.getElementById("mock-table-tbody");
    if (!tbody) return;

    const tr = document.createElement("tr");
    tr.style.background = decision === "BLOCK" ? "rgba(239, 68, 68, 0.15)" : "rgba(255, 255, 255, 0.05)";
    const now = new Date().toLocaleTimeString();

    tr.innerHTML = `
        <td style="color:#64748B;">${now}</td>
        <td style="font-family:'JetBrains Mono'; color:#94A3B8;">${id}</td>
        <td><strong>${vpa}</strong></td>
        <td>${loc}</td>
        <td><strong>${amt}</strong></td>
        <td><span style="color:#EF4444; font-weight:700;">${score}</span></td>
        <td><span class="mock-badge-decision ${decision}">${decision}</span></td>
        <td style="color:#F87171;">${reason}</td>
    `;

    tbody.insertBefore(tr, tbody.firstChild);
}

// ================= PLAYBACK ORCHESTRATOR =================
function togglePlayPause() {
    if (isPlaying) pauseVideo();
    else playVideo();
}

function playVideo() {
    isPlaying = true;
    document.getElementById("play-icon").className = "fa-solid fa-pause";
    startScene(currentSceneIndex);
    startTimer();
}

function pauseVideo() {
    isPlaying = false;
    document.getElementById("play-icon").className = "fa-solid fa-play";
    if (synth) synth.cancel();
    clearInterval(sceneTimer);
}

function startScene(sceneIdx) {
    if (synth) synth.cancel();

    const scene = WALKTHROUGH_SCENES[sceneIdx];
    document.getElementById("slide-indicator").innerText = `Scene ${scene.id + 1} of ${WALKTHROUGH_SCENES.length}: ${scene.title}`;
    document.getElementById("live-caption-text").innerText = scene.caption;

    // Trigger dynamic graph and visual application animations
    scene.action();

    if (!isMuted && 'speechSynthesis' in window) {
        currentUtterance = new SpeechSynthesisUtterance(scene.narration);
        currentUtterance.rate = 1.02 * playbackSpeed;
        currentUtterance.pitch = 1.0;

        const voices = synth.getVoices();
        const preferredVoice = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Google") || v.name.includes("Natural") || v.name.includes("Samantha") || v.name.includes("Daniel") || v.name.includes("David")));
        if (preferredVoice) currentUtterance.voice = preferredVoice;

        // Seamless transition on audio finish
        currentUtterance.onend = () => {
            if (isPlaying) {
                setTimeout(() => {
                    if (isPlaying && currentSceneIndex < WALKTHROUGH_SCENES.length - 1) {
                        nextScene();
                    } else if (currentSceneIndex >= WALKTHROUGH_SCENES.length - 1) {
                        pauseVideo();
                        currentElapsedSeconds = totalDurationSeconds;
                        updateProgressBar();
                        updateTimeDisplay();
                    }
                }, 400);
            }
        };

        synth.speak(currentUtterance);
    }
}

function startTimer() {
    clearInterval(sceneTimer);
    sceneTimer = setInterval(() => {
        currentElapsedSeconds += 1;
        updateProgressBar();
        updateTimeDisplay();
    }, 1000 / playbackSpeed);
}

function nextScene() {
    if (currentSceneIndex < WALKTHROUGH_SCENES.length - 1) {
        currentSceneIndex++;
        let acc = 0;
        for (let i = 0; i < currentSceneIndex; i++) acc += SCENE_DURATIONS[i];
        currentElapsedSeconds = acc;

        updateSceneView();
        if (isPlaying) startScene(currentSceneIndex);
    }
}

function prevScene() {
    if (currentSceneIndex > 0) {
        currentSceneIndex--;
        let acc = 0;
        for (let i = 0; i < currentSceneIndex; i++) acc += SCENE_DURATIONS[i];
        currentElapsedSeconds = acc;

        updateSceneView();
        if (isPlaying) startScene(currentSceneIndex);
    }
}

function updateSceneView() {
    const scene = WALKTHROUGH_SCENES[currentSceneIndex];
    document.getElementById("slide-indicator").innerText = `Scene ${scene.id + 1} of ${WALKTHROUGH_SCENES.length}: ${scene.title}`;
    document.getElementById("live-caption-text").innerText = scene.caption;
    scene.action();
}

function updateProgressBar() {
    const pct = Math.min((currentElapsedSeconds / totalDurationSeconds) * 100, 100);
    document.getElementById("video-progress").style.width = `${pct}%`;
}

function updateTimeDisplay() {
    const curMins = Math.floor(currentElapsedSeconds / 60);
    const curSecs = Math.floor(currentElapsedSeconds % 60).toString().padStart(2, '0');
    const totMins = Math.floor(totalDurationSeconds / 60);
    const totSecs = Math.floor(totalDurationSeconds % 60).toString().padStart(2, '0');
    document.getElementById("time-display").innerText = `${curMins}:${curSecs} / ${totMins}:${totSecs}`;
}

function seekVideo(evt) {
    const bar = evt.currentTarget;
    const rect = bar.getBoundingClientRect();
    const clickX = evt.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));

    currentElapsedSeconds = ratio * totalDurationSeconds;

    let acc = 0;
    for (let i = 0; i < WALKTHROUGH_SCENES.length; i++) {
        acc += SCENE_DURATIONS[i];
        if (currentElapsedSeconds <= acc) {
            currentSceneIndex = i;
            break;
        }
    }

    updateSceneView();
    updateProgressBar();
    updateTimeDisplay();
    if (isPlaying) startScene(currentSceneIndex);
}

function toggleMute() {
    isMuted = !isMuted;
    document.getElementById("volume-icon").className = isMuted ? "fa-solid fa-volume-xmark" : "fa-solid fa-volume-high";
    if (isMuted && synth) synth.cancel();
    else if (!isMuted && isPlaying) startScene(currentSceneIndex);
}

function changeSpeed(val) {
    playbackSpeed = parseFloat(val);
    if (isPlaying) {
        startTimer();
        startScene(currentSceneIndex);
    }
}

function toggleFullscreen() {
    const el = document.getElementById("video-canvas-container");
    if (!document.fullscreenElement) {
        if (el.requestFullscreen) el.requestFullscreen();
    } else {
        if (document.exitFullscreen) document.exitFullscreen();
    }
}

// ================= 1-CLICK VIDEO RECORDER & DOWNLOAD ENGINE =================
async function toggleVideoRecording() {
    const btn = document.getElementById("btn-export-video");
    const text = document.getElementById("record-btn-text");

    if (isRecording) {
        if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
        isRecording = false;
        btn.style.background = "linear-gradient(135deg, #EF4444, #8B5CF6)";
        text.innerText = "Record & Download Video (.webm)";
    } else {
        try {
            const stream = await navigator.mediaDevices.getDisplayMedia({
                video: { mediaSource: "screen", width: 1920, height: 1080 },
                audio: true
            });

            recordedChunks = [];
            mediaRecorder = new MediaRecorder(stream, { mimeType: "video/webm; codecs=vp9" });

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) recordedChunks.push(e.data);
            };

            mediaRecorder.onstop = () => {
                const blob = new Blob(recordedChunks, { type: "video/webm" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "GhostBuster_AI_Animated_Application_Demo.webm";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            };

            mediaRecorder.start();
            isRecording = true;
            btn.style.background = "#10B981";
            text.innerText = "🔴 Recording... (Click to Finish & Save)";

            currentSceneIndex = 0;
            currentElapsedSeconds = 0;
            updateSceneView();
            playVideo();

        } catch (err) {
            alert("Video capture started. Please select the current browser tab to capture high-definition video!");
            console.error("Screen recording error:", err);
        }
    }
}
