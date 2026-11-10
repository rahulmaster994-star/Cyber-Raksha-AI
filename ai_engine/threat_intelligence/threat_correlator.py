"""
threat_correlator.py — Stage 8 Unified Risk & Evidence Correlation
Correlates evidence across Stage 2 (URL), Stage 3 (NLP/Digital Arrest),
Stage 4 (Audio Deepfake), and Threat Intelligence Feeds.

Applies strict principles:
  - Corroborates independent detection vectors without double-counting.
  - Distinguishes factual findings from heuristic model predictions.
  - Distinguishes negative findings from unavailable external information.
  - Resolves conflicts between heuristic models and verified threat intelligence.
  - Emits clear limitations and uncertainty factors. Never manufactures certainty.
"""
from typing import Dict, Any, List, Optional
from ai_engine.threat_intelligence.indicator_extractor import extract_indicators
from ai_engine.threat_intelligence.threat_database import match_all_indicators


class ThreatCorrelator:
    @staticmethod
    def correlate_evidence(
        url_result: Optional[Dict[str, Any]] = None,
        comm_result: Optional[Dict[str, Any]] = None,
        audio_result: Optional[Dict[str, Any]] = None,
        extracted_indicators: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes multiple detection outputs into an interconnected, defensible evidence graph.
        """
        evidence_chain: List[Dict[str, Any]] = []
        factual_evidence: List[str] = []
        model_predictions: List[str] = []
        negative_findings: List[str] = []
        unavailable_information: List[str] = []
        uncertainty_factors: List[str] = []
        limitations: List[str] = []
        threat_vectors: List[str] = []
        is_corroborated = False
        corroboration_notes: List[str] = []
        conflict_notes: List[str] = []

        # 1. Threat Intelligence Layer
        intel_matches = []
        if extracted_indicators:
            intel_matches = match_all_indicators(extracted_indicators)
            if intel_matches:
                for match in intel_matches:
                    fact = (
                        f"Verified IoC match: {match.get('indicator_type')} '{match.get('indicator_value')}' "
                        f"listed in {match.get('source_name')} as {match.get('threat_type')} "
                        f"(Severity: {match.get('severity')})"
                    )
                    factual_evidence.append(fact)
                    evidence_chain.append({
                        "layer": "THREAT_INTEL",
                        "type": "FACT",
                        "severity": match.get("severity", "HIGH"),
                        "title": f"Known Malicious Indicator: {match.get('source_name')}",
                        "details": fact,
                        "source": match.get("source_name")
                    })
                    threat_vectors.append(f"INTEL_{match.get('threat_type')}")
            else:
                total_inds = sum(len(v) for v in extracted_indicators.values())
                if total_inds > 0:
                    unavailable_information.append(
                        f"Searched {total_inds} extracted indicator(s) against local verified threat intelligence cache; no matching IoC found. (Note: Newly created or targeted zero-day threats may not yet appear in threat feeds.)"
                    )

        # 2. Stage 2 URL Detection Layer
        if url_result:
            u_class = url_result.get("classification", "LEGITIMATE")
            u_score = url_result.get("risk_score", 0.0)
            u_level = url_result.get("risk_level", "LOW")
            u_conf = url_result.get("confidence", 0.0)
            u_indicators = url_result.get("risk_indicators", [])

            # Factual indicators from lexical analysis
            for ind in u_indicators:
                factual_evidence.append(f"URL structural finding: {ind}")

            model_predictions.append(
                f"RandomForest URL Classifier: {u_class} (Risk Score: {u_score}/100, Model Confidence: {u_conf*100:.1f}%)"
            )

            if u_level in ["HIGH", "CRITICAL", "SUSPICIOUS"]:
                evidence_chain.append({
                    "layer": "STAGE_2_URL",
                    "type": "PREDICTION",
                    "severity": u_level,
                    "title": f"URL Classifier: {u_class}",
                    "details": f"Machine learning URL model calculated risk score {u_score}/100 based on structural/entropy features.",
                    "source": "RandomForest URL Classifier"
                })
                threat_vectors.append("WEB_PHISHING")
            else:
                negative_findings.append("URL structural analysis identified no deceptive domain or credential harvesting patterns.")

        # 3. Stage 3 Communication NLP Layer
        if comm_result:
            c_class = comm_result.get("classification", "SAFE")
            c_score = comm_result.get("risk_score", 0.0)
            c_level = comm_result.get("risk_level", "LOW")
            c_indicators = comm_result.get("detected_indicators", [])
            c_conf = comm_result.get("confidence", 0.0)

            for ind in c_indicators:
                factual_evidence.append(f"Communication pattern detected: {ind}")

            model_predictions.append(
                f"LinearSVC Communication Classifier: {c_class} (Risk Score: {c_score}/100, Confidence: {c_conf*100:.1f}%)"
            )

            if c_level in ["HIGH", "CRITICAL", "SUSPICIOUS"] or c_class in ["DIGITAL_ARREST", "COMMUNICATION_FRAUD", "SCAM_MESSAGE"]:
                evidence_chain.append({
                    "layer": "STAGE_3_NLP",
                    "type": "PREDICTION",
                    "severity": c_level,
                    "title": f"Social Engineering & Coercion: {c_class}",
                    "details": f"NLP threat model identified {len(c_indicators)} manipulation pattern(s) (Score: {c_score}/100).",
                    "source": "LinearSVC Communication Detector"
                })
                if "DIGITAL_ARREST" in c_class:
                    threat_vectors.append("DIGITAL_ARREST_COERCION")
                else:
                    threat_vectors.append("SOCIAL_ENGINEERING")
            else:
                negative_findings.append("Communication analysis identified no urgency coercion or impersonation signatures.")

        # 4. Stage 4 Audio Analysis Layer
        if audio_result:
            a_class = audio_result.get("classification", "LIKELY_NATURAL")
            a_score = audio_result.get("risk_score", 0.0)
            a_level = audio_result.get("risk_level", "LOW")
            a_inconclusive = audio_result.get("is_inconclusive", False)

            if a_inconclusive:
                uncertainty_factors.append(
                    "Audio sample quality or duration insufficient for definitive acoustic artifact analysis."
                )
                unavailable_information.append("Acoustic deepfake determination could not be completed with high confidence.")
            else:
                model_predictions.append(
                    f"Acoustic Vocoder Classifier: {a_class} (Risk Score: {a_score}/100)"
                )
                if a_level in ["HIGH", "CRITICAL", "MEDIUM"]:
                    evidence_chain.append({
                        "layer": "STAGE_4_AUDIO",
                        "type": "PREDICTION",
                        "severity": a_level,
                        "title": f"Synthetic Voice / Deepfake: {a_class}",
                        "details": f"Acoustic spectrogram analysis detected spectral boundary/vocoder anomalies (Score: {a_score}/100).",
                        "source": "RandomForest Acoustic Classifier"
                    })
                    threat_vectors.append("VOICE_CLONING_IMPERSONATION")
                else:
                    negative_findings.append("Acoustic analysis detected no significant vocoder or phase continuity artifacts.")

            limitations.append(
                "Audio analysis detects synthetic generation artifacts only; it DOES NOT identify the speaker's true biometric identity."
            )

        # 5. Multi-Vector Corroboration Logic
        # Case A: Malicious URL inside coercive message
        if url_result and comm_result:
            u_bad = url_result.get("risk_level") in ["HIGH", "CRITICAL"] or url_result.get("risk_score", 0) >= 60
            c_bad = comm_result.get("risk_level") in ["HIGH", "CRITICAL"] or comm_result.get("risk_score", 0) >= 60
            if u_bad and c_bad:
                is_corroborated = True
                corroboration_notes.append(
                    "Cross-Vector Confirmation: Malicious link confirmed embedded within an actively coercive message."
                )

        # Case B: Threat Intel match + Model Heuristic
        if intel_matches and (url_result or comm_result):
            is_corroborated = True
            corroboration_notes.append(
                f"External IoC Corroboration: Extracted indicator matches active threat feed ({intel_matches[0].get('source_name')})."
            )

        # Case C: Voice Cloning + Financial Fraud request
        if audio_result and comm_result:
            a_bad = audio_result.get("risk_score", 0) >= 60
            c_bad = comm_result.get("risk_score", 0) >= 50
            if a_bad and c_bad:
                is_corroborated = True
                corroboration_notes.append(
                    "Multi-Modal Impersonation: Synthetic voice cloning combined with financial manipulation request."
                )

        # 6. Conflict Resolution Logic
        # Conflict 1: Model says benign but Threat Intel has verified match
        if intel_matches and url_result and url_result.get("risk_level") in ["LOW", "MEDIUM"]:
            conflict_notes.append(
                "Conflict Resolution: URL classifier scored low on lexical heuristics, but an active threat intelligence feed confirms this exact indicator as malicious. Verified threat intelligence takes precedence."
            )

        # Conflict 2: Model says HIGH but Threat Intel has no match
        if not intel_matches and url_result and url_result.get("risk_level") in ["HIGH", "CRITICAL"]:
            conflict_notes.append(
                "Note on Novel Threat: Zero external IoC matches found in threat feeds; risk assessment is driven by structural and lexical anomalies. Newly registered phishing domains often lack public threat feed records."
            )

        # General Platform Limitations
        limitations.append(
            "Detection scores represent statistical risk probabilities based on available training data; they are not absolute guarantees of safety or malice."
        )

        return {
            "evidence_chain": evidence_chain,
            "factual_evidence": factual_evidence,
            "model_predictions": model_predictions,
            "negative_findings": negative_findings,
            "unavailable_information": unavailable_information,
            "uncertainty_factors": uncertainty_factors,
            "limitations": limitations,
            "conflict_notes": conflict_notes,
            "threat_vectors": list(set(threat_vectors)),
            "intel_matches": intel_matches,
            "intel_matches_count": len(intel_matches),
            "is_corroborated": is_corroborated,
            "corroboration_notes": corroboration_notes,
            "active_modules_count": sum(1 for m in [url_result, comm_result, audio_result] if m is not None)
        }
