"""
Device & Network Fingerprint Risk Analyzer
Evaluates canvas entropy, VPN/Tor/Proxy nodes, and emulator signatures.
"""

import re
from typing import Dict, Any
from models.transaction import DeviceFingerprint


class DeviceFingerprintService:
    KNOWN_TOR_EXIT_IPS = {"185.220.101.5", "198.98.56.12", "192.42.116.16", "51.15.43.205"}
    KNOWN_DATACENTER_ASNS = {"AS14061", "AS16509", "AS15169", "AS8075"}
    KNOWN_EMULATOR_PATTERNS = ["qemu", "vbox", "nox", "bluestacks", "genymotion", "goldfish"]

    @classmethod
    def evaluate_fingerprint(cls, device: DeviceFingerprint) -> Dict[str, Any]:
        """
        Analyzes device authenticity and network reputation.
        Returns risk score (0-100) and specific risk tags.
        """
        risk_score = 0.0
        flags = []

        # 1. Tor Exit Node Check
        if device.is_tor or device.ip_address in cls.KNOWN_TOR_EXIT_IPS:
            risk_score += 85.0
            flags.append("TOR_ANONYMIZED_NETWORK")

        # 2. Commercial / Data Center VPN Check
        if device.is_vpn:
            risk_score += 45.0
            flags.append("ANONYMOUS_VPN_DETECTED")

        # 3. Android / iOS Emulator Check
        ua_lower = device.user_agent.lower()
        if device.is_emulator or any(em in ua_lower for em in cls.KNOWN_EMULATOR_PATTERNS):
            risk_score += 70.0
            flags.append("DEVICE_EMULATOR_SPOOFING")

        # 4. Canvas Hash Mismatch / Missing Entropy
        if not device.canvas_hash or device.canvas_hash == "00000000":
            risk_score += 35.0
            flags.append("INCONSISTENT_CANVAS_FINGERPRINT")

        # 5. Outdated / Headless Browser User-Agent Check
        if "headless" in ua_lower or "phantomjs" in ua_lower or "puppeteer" in ua_lower or "selenium" in ua_lower:
            risk_score += 90.0
            flags.append("AUTOMATED_HEADLESS_BOTNET")

        clamped_score = min(max(risk_score, 0.0), 100.0)
        return {
            "device_risk_score": round(clamped_score, 2),
            "flags": flags,
            "is_high_risk": clamped_score >= 60.0
        }


device_fingerprint_service = DeviceFingerprintService()
