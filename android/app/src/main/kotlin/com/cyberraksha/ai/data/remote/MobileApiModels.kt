package com.cyberraksha.ai.data.remote

import com.google.gson.annotations.SerializedName

// ── SMS Analysis DTOs ─────────────────────────────────────────────────────────

data class MessageAnalysisRequest(
    @SerializedName("device_id")    val deviceId: String,
    @SerializedName("message_text") val messageText: String,
    @SerializedName("sender")       val sender: String? = null
)

data class ExtractedUrlThreat(
    @SerializedName("url")          val url: String,
    @SerializedName("is_malicious") val isMalicious: Boolean,
    @SerializedName("threat_type")  val threatType: String?,
    @SerializedName("source")       val source: String?
)

data class MessageAnalysisResponse(
    @SerializedName("message_hash")       val messageHash: String,
    @SerializedName("risk_score")         val riskScore: Float,
    @SerializedName("risk_level")         val riskLevel: String,
    @SerializedName("fraud_category")     val fraudCategory: String,
    @SerializedName("detection_reasons")  val detectionReasons: List<String>,
    @SerializedName("extracted_urls")     val extractedUrls: List<String>,
    @SerializedName("url_threats")        val urlThreats: List<ExtractedUrlThreat>,
    @SerializedName("recommended_action") val recommendedAction: String,
    @SerializedName("analyzed_at")        val analyzedAt: String
)

// ── Call & Phone Reputation DTOs ─────────────────────────────────────────────

data class NumberCheckRequest(
    @SerializedName("device_id")    val deviceId: String,
    @SerializedName("phone_number") val phoneNumber: String
)

data class NumberCheckResponse(
    @SerializedName("phone_number")           val phoneNumber: String,
    @SerializedName("normalized_number")      val normalizedNumber: String,
    @SerializedName("risk_level")             val riskLevel: String,
    @SerializedName("fraud_category")         val fraudCategory: String?,
    @SerializedName("report_count")           val reportCount: Int,
    @SerializedName("confidence_score")       val confidenceScore: Float,
    @SerializedName("source")                 val source: String,
    @SerializedName("notes")                  val notes: String?,
    @SerializedName("recommended_action")     val recommendedAction: String,
    @SerializedName("checked_at")             val checkedAt: String,
    @SerializedName("is_verified_authority")  val isVerifiedAuthority: Boolean = false,
    @SerializedName("classification_reason")  val classificationReason: String? = null,
    @SerializedName("dispute_count")          val disputeCount: Int = 0
)

// ── Threat History DTOs ───────────────────────────────────────────────────────

data class ThreatHistoryItem(
    @SerializedName("id")                val id: Int,
    @SerializedName("threat_type")       val threatType: String,
    @SerializedName("target_or_hash")    val targetOrHash: String,
    @SerializedName("risk_level")        val riskLevel: String,
    @SerializedName("risk_score")        val riskScore: Float,
    @SerializedName("fraud_category")    val fraudCategory: String,
    @SerializedName("detection_reasons") val detectionReasons: List<String>,
    @SerializedName("timestamp")         val timestamp: String
)

data class ThreatHistoryResponse(
    @SerializedName("device_id") val deviceId: String,
    @SerializedName("total")     val total: Int,
    @SerializedName("items")     val items: List<ThreatHistoryItem>
)

// ── Protection Status DTOs ───────────────────────────────────────────────────

data class ProtectionStatusResponse(
    @SerializedName("device_id")                  val deviceId: String,
    @SerializedName("sms_protection")             val smsProtection: String,
    @SerializedName("call_protection")            val callProtection: String,
    @SerializedName("database_signatures_count") val databaseSignaturesCount: Int,
    @SerializedName("phone_reputation_entries")   val phoneReputationEntries: Int,
    @SerializedName("last_sync")                  val lastSync: String?
)

// ── Threat Reporting DTOs ─────────────────────────────────────────────────────

data class ReportThreatRequest(
    @SerializedName("device_id")       val deviceId: String,
    @SerializedName("threat_type")     val threatType: String,
    @SerializedName("indicator_value") val indicatorValue: String,
    @SerializedName("fraud_category")  val fraudCategory: String? = null,
    @SerializedName("description")     val description: String? = null
)

data class ReportThreatResponse(
    @SerializedName("success")         val success: Boolean,
    @SerializedName("message")         val message: String,
    @SerializedName("indicator_value") val indicatorValue: String,
    @SerializedName("report_id")       val reportId: Int?
)

// ── Dispute DTOs (Phase B2.1) ──────────────────────────────────────────────────

data class DisputeNumberRequest(
    @SerializedName("device_id")    val deviceId: String,
    @SerializedName("phone_number") val phoneNumber: String,
    @SerializedName("reason")       val reason: String? = null
)

data class DisputeNumberResponse(
    @SerializedName("success")            val success: Boolean,
    @SerializedName("message")            val message: String,
    @SerializedName("phone_number")       val phoneNumber: String,
    @SerializedName("current_risk_level") val currentRiskLevel: String,
    @SerializedName("dispute_count")      val disputeCount: Int
)

// ── SMS Reception Mode (Phase B2.1 — Accuracy Documentation) ─────────────────

/**
 * Documents the actual SMS interception capability of this application.
 *
 * MANUAL_ONLY: User manually pastes or shares a suspicious SMS for analysis.
 *              Automatic interception via RECEIVE_SMS BroadcastReceiver is NOT implemented.
 *              This is the ONLY mode available as of Phase B2.1.
 *
 * SHARE_TARGET: User shares SMS content via Android share sheet to Cyber Raksha AI.
 *               Planned for a future phase.
 *
 * AUTOMATIC_FOREGROUND: Real-time interception via default SMS role (READ_SMS + RECEIVE_SMS).
 *                        Requires default SMS app designation. NOT implemented in B2.1.
 *                        Subject to strict Google Play policy review.
 */
enum class SmsReceptionMode {
    MANUAL_ONLY,       // Current state — B2.1
    SHARE_TARGET,      // Future — planned
    AUTOMATIC_FOREGROUND  // Future — requires default SMS role
}

// ── Unified Security Event DTOs (Phase B3) ──────────────────────────────────

data class SecurityEventApiRequest(
    @SerializedName("event_type")        val eventType: String,
    @SerializedName("severity")          val severity: String,
    @SerializedName("source_component")  val sourceComponent: String = "ANDROID_APP",
    @SerializedName("device_id")         val deviceId: String? = null,
    @SerializedName("threat_indicator")  val threatIndicator: String? = null,
    @SerializedName("risk_score")        val riskScore: Float = 0.0f,
    @SerializedName("detection_reason")  val detectionReason: String? = null,
    @SerializedName("description")       val description: String,
    @SerializedName("raw_payload")       val rawPayload: String? = null
)

data class SecurityEventApiResponse(
    @SerializedName("id")                  val id: Int,
    @SerializedName("event_id")            val eventId: String,
    @SerializedName("event_type")          val eventType: String,
    @SerializedName("severity")            val severity: String,
    @SerializedName("source_component")    val sourceComponent: String,
    @SerializedName("device_id")           val deviceId: String?,
    @SerializedName("threat_indicator")    val threatIndicator: String?,
    @SerializedName("risk_score")          val riskScore: Float,
    @SerializedName("detection_reason")    val detectionReason: String?,
    @SerializedName("description")         val description: String,
    @SerializedName("is_resolved")         val isResolved: Boolean,
    @SerializedName("verification_status") val verificationStatus: String,
    @SerializedName("incident_id")         val incidentId: Int?,
    @SerializedName("processing_status")   val processingStatus: String,
    @SerializedName("created_at")          val createdAt: String
)


