"""
intelligence_engine.py — Stage 8 Unified Risk Engine
Orchestrates multi-vector risk assessment, evidence synthesis,
mathematical corroboration scoring, conflict resolution, and actionable recommendations.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ai_engine.threat_intelligence.indicator_extractor import extract_indicators
from ai_engine.threat_intelligence.threat_database import match_all_indicators, get_intel_stats
from ai_engine.threat_intelligence.threat_correlator import ThreatCorrelator

# Import Stage 2, 3, 4 detectors for combined analysis
from ai_engine.inference.phishing_detector import detect_phishing
from ai_engine.inference.communication_detector import communication_detector
from ai_engine.inference.audio_detector import audio_detector


class IntelligenceEngine:
    """
    Central Threat Intelligence & Unified Risk Assessment Engine.
    """

    def analyze_unified(
        self,
        url: Optional[str] = None,
        message: Optional[str] = None,
        is_digital_arrest: bool = False,
        audio_bytes: Optional[bytes] = None,
        audio_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Takes one or more threat inputs, runs underlying specialized AI models,
        correlates threat intelligence, handles conflicts, and produces a mathematically
        calibrated unified score.
        """
        url_result: Optional[Dict[str, Any]] = None
        comm_result: Optional[Dict[str, Any]] = None
        audio_result: Optional[Dict[str, Any]] = None
        extracted_indicators: Dict[str, List[str]] = {"urls": [], "domains": [], "ips": [], "upi_ids": [], "phones": []}

        # Step 1: Handle Message
        if message and message.strip():
            msg_text = message.strip()
            extracted_indicators = extract_indicators(msg_text)

            comm_raw = communication_detector.analyze_message(msg_text)
            comm_result = {
                "classification": comm_raw.get("classification", "SAFE"),
                "risk_level": comm_raw.get("risk_level", "LOW"),
                "risk_score": comm_raw.get("risk_score", 0.0),
                "confidence": comm_raw.get("confidence", 0.5),
                "detected_indicators": comm_raw.get("detected_indicators", []),
                "explanation": comm_raw.get("explanation", "")
            }

            # If user didn't explicitly provide a URL, but the message has one, automatically analyze the first extracted URL
            if not url and extracted_indicators["urls"]:
                url = extracted_indicators["urls"][0]

        # Step 2: Handle URL
        if url and url.strip():
            target_url = url.strip()
            if target_url not in extracted_indicators["urls"]:
                extracted_indicators["urls"].append(target_url)
                extracted_indicators.update(extract_indicators(target_url))

            u_raw = detect_phishing(target_url)
            url_result = {
                "classification": u_raw.classification,
                "risk_level": u_raw.risk_level,
                "risk_score": u_raw.risk_score,
                "confidence": u_raw.confidence,
                "recommendation": u_raw.recommendation,
                "risk_indicators": u_raw.analysis.get("risk_indicators", [])
            }

        # Step 3: Handle Audio
        if audio_bytes and len(audio_bytes) > 0:
            fn = audio_filename or "unified_voice.wav"
            audio_raw = audio_detector.analyze_audio(audio_bytes, filename=fn)
            audio_result = audio_raw

        # Step 4: Evidence Correlation
        correlation = ThreatCorrelator.correlate_evidence(
            url_result=url_result,
            comm_result=comm_result,
            audio_result=audio_result,
            extracted_indicators=extracted_indicators
        )

        # Step 5: Compute Unified Calibrated Risk Score
        unified_score, unified_level, threat_category = self._calculate_unified_risk(
            url_result=url_result,
            comm_result=comm_result,
            audio_result=audio_result,
            correlation=correlation
        )

        # Step 6: Synthesize Evidence Summary & Actionable Recommendations
        explanation = self._generate_unified_explanation(
            unified_level=unified_level,
            unified_score=unified_score,
            threat_category=threat_category,
            correlation=correlation,
            url_result=url_result,
            comm_result=comm_result,
            audio_result=audio_result
        )

        recommendations = self._generate_unified_recommendations(
            unified_level=unified_level,
            threat_category=threat_category,
            correlation=correlation
        )

        return {
            "overall_risk_level": unified_level,
            "overall_risk_score": round(unified_score, 1),
            "threat_category": threat_category,
            "is_corroborated": correlation["is_corroborated"],
            "corroboration_notes": correlation["corroboration_notes"],
            "intel_matches_count": correlation["intel_matches_count"],
            "intel_matches": correlation["intel_matches"],
            "evidence_chain": correlation["evidence_chain"],
            "factual_evidence": correlation["factual_evidence"],
            "model_predictions": correlation["model_predictions"],
            "negative_findings": correlation["negative_findings"],
            "unavailable_information": correlation["unavailable_information"],
            "uncertainty_factors": correlation["uncertainty_factors"],
            "limitations": correlation["limitations"],
            "conflict_notes": correlation["conflict_notes"],
            "extracted_indicators": extracted_indicators,
            "modules": {
                "url_detection": url_result,
                "communication_threat": comm_result,
                "audio_detection": audio_result
            },
            "explanation": explanation,
            "recommended_actions": recommendations,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _calculate_unified_risk(
        self,
        url_result: Optional[Dict],
        comm_result: Optional[Dict],
        audio_result: Optional[Dict],
        correlation: Dict
    ) -> tuple[float, str, str]:
        """
        Calibrated Multi-Factor Scoring Methodology:
        1. Base score = highest individual module severity (prevents dilution).
        2. Threat Intel match = verified malicious IoC enforces minimum score of 80.0 (CRITICAL/HIGH).
        3. Corroboration boost = +15 points if two independent vectors confirm fraud.
        4. Inconclusive handling = if audio is inconclusive and no other inputs, return INCONCLUSIVE.
        5. Clamped to [0.0, 100.0].
        """
        scores = []
        categories = []

        if url_result:
            scores.append(url_result.get("risk_score", 0.0))
            if url_result.get("risk_score", 0.0) >= 50:
                categories.append("Phishing Web Threat")

        if comm_result:
            scores.append(comm_result.get("risk_score", 0.0))
            c_class = comm_result.get("classification", "")
            if "DIGITAL_ARREST" in c_class:
                categories.append("Digital Arrest Extortion")
            elif comm_result.get("risk_score", 0.0) >= 50:
                categories.append("Communication Fraud")

        if audio_result and not audio_result.get("is_inconclusive"):
            scores.append(audio_result.get("risk_score", 0.0))
            if audio_result.get("risk_score", 0.0) >= 50:
                categories.append("Voice Cloning Impersonation")

        # Inconclusive check
        if not scores:
            if audio_result and audio_result.get("is_inconclusive"):
                return 40.0, "MEDIUM", "Inconclusive Audio / Insufficient Evidence"
            return 0.0, "LOW", "Benign / Low Risk"

        base_score = max(scores)

        # Conflict resolution / Override: verified IoC match takes precedence
        if correlation.get("intel_matches_count", 0) > 0:
            # Enforce at least 80 points when confirmed in verified threat database
            base_score = max(base_score, 80.0)
            if "Verified Threat IoC" not in categories:
                categories.append("Verified Threat Feed Match")

        # Multi-vector corroboration boost
        boost = 0.0
        if correlation.get("is_corroborated"):
            boost += 15.0

        final_score = min(100.0, max(0.0, base_score + boost))

        # Risk level thresholds
        if final_score >= 80.0:
            level = "CRITICAL"
        elif final_score >= 60.0:
            level = "HIGH"
        elif final_score >= 35.0:
            level = "MEDIUM"
        else:
            level = "LOW"

        category = " & ".join(categories) if categories else "Low Risk / Benign"

        return final_score, level, category

    def _generate_unified_explanation(
        self,
        unified_level: str,
        unified_score: float,
        threat_category: str,
        correlation: Dict,
        url_result: Optional[Dict],
        comm_result: Optional[Dict],
        audio_result: Optional[Dict]
    ) -> str:
        parts = []
        parts.append(
            f"Overall Assessment: {unified_level} RISK (Unified Threat Score: {unified_score:.1f}/100) — {threat_category}."
        )

        if correlation.get("conflict_notes"):
            parts.extend(correlation["conflict_notes"])

        if correlation.get("corroboration_notes"):
            parts.extend(correlation["corroboration_notes"])

        if correlation.get("intel_matches"):
            match_srcs = [f"{m.get('source_name')} ({m.get('threat_type')})" for m in correlation["intel_matches"]]
            parts.append(f"Threat Intelligence Feed Confirmation: Indicators verified in {', '.join(match_srcs)}.")

        return " ".join(parts)

    def _generate_unified_recommendations(
        self,
        unified_level: str,
        threat_category: str,
        correlation: Dict
    ) -> List[str]:
        recs = []

        if unified_level in ["CRITICAL", "HIGH"]:
            recs.append("DO NOT click any links, download attachments, or call provided numbers.")
            recs.append("DO NOT transfer funds, share OTPs, or agree to video calls under duress.")
            if "Digital Arrest" in threat_category:
                recs.append("Report immediately to the National Cyber Crime Reporting Portal (1930 / cybercrime.gov.in).")
                recs.append("Remember: Indian Law Enforcement agencies NEVER conduct court proceedings or arrests over Skype/WhatsApp.")
            if "Voice Cloning" in threat_category:
                recs.append("Hang up immediately and contact the alleged person/executive on a known verified offline line.")
            if correlation.get("intel_matches_count", 0) > 0:
                recs.append("Block the associated domain/IP address at your perimeter firewall or DNS resolver.")
        elif unified_level == "MEDIUM":
            recs.append("Exercise caution. Verify the sender's identity through an independent channel before replying.")
            recs.append("Inspect any requested financial actions with a verified family member or company compliance team.")
        else:
            recs.append("No immediate threats detected. Maintain standard cybersecurity hygiene.")

        return recs


intelligence_engine = IntelligenceEngine()
