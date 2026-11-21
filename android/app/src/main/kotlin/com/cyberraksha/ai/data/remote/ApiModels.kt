package com.cyberraksha.ai.data.remote

import com.google.gson.annotations.SerializedName

// ── Device ────────────────────────────────────────────────────────────────────

data class DeviceRegisterRequest(
    @SerializedName("device_id")   val deviceId: String,
    @SerializedName("device_name") val deviceName: String,
    @SerializedName("app_version") val appVersion: String = "1.0.0"
)

data class ProtectionModulesStatus(
    @SerializedName("url_phishing")        val urlPhishing: Boolean = true,
    @SerializedName("communication_fraud") val communicationFraud: Boolean = true,
    @SerializedName("threat_intel")        val threatIntel: Boolean = true,
    @SerializedName("notifications")       val notifications: Boolean = true,
    @SerializedName("sms_detection")       val smsDetection: Boolean = false,
    @SerializedName("call_detection")      val callDetection: Boolean = false
)

data class DeviceRegistrationResponse(
    @SerializedName("device_id")          val deviceId: String,
    @SerializedName("device_name")        val deviceName: String,
    @SerializedName("status")             val status: String,
    @SerializedName("registered_at")      val registeredAt: String,
    @SerializedName("protection_modules") val protectionModules: ProtectionModulesStatus?,
    @SerializedName("device_token")       val deviceToken: String? = null
)

data class DeviceStatusResponse(
    @SerializedName("device_id")          val deviceId: String,
    @SerializedName("device_name")        val deviceName: String,
    @SerializedName("status")             val status: String,
    @SerializedName("security_posture")   val securityPosture: String,
    @SerializedName("last_seen_at")       val lastSeenAt: String?,
    @SerializedName("registered_at")      val registeredAt: String,
    @SerializedName("protection_modules") val protectionModules: ProtectionModulesStatus?
)

data class SecurityEventItem(
    @SerializedName("id")               val id: Int,
    @SerializedName("event_type")       val eventType: String,
    @SerializedName("severity")         val severity: String,
    @SerializedName("description")      val description: String,
    @SerializedName("target_domain")    val targetDomain: String?,
    @SerializedName("created_at")       val createdAt: String
)

data class DeviceActivityListResponse(
    @SerializedName("device_id") val deviceId: String,
    @SerializedName("events")    val events: List<SecurityEventItem>,
    @SerializedName("total")     val total: Int
)

// ── Notifications ─────────────────────────────────────────────────────────────

data class NotificationItem(
    @SerializedName("id")               val id: Int,
    @SerializedName("title")            val title: String,
    @SerializedName("message")          val message: String,
    @SerializedName("severity")         val severity: String,
    @SerializedName("category")         val category: String?,
    @SerializedName("target_domain")    val targetDomain: String?,
    @SerializedName("is_read")          val isRead: Boolean,
    @SerializedName("created_at")       val createdAt: String,
    @SerializedName("source_component") val sourceComponent: String?
)

data class NotificationListResponse(
    @SerializedName(value = "notifications", alternate = ["items"]) val notifications: List<NotificationItem>? = emptyList(),
    @SerializedName("total")         val total: Int = 0,
    @SerializedName("unread_count")  val unreadCount: Int = 0
)

data class UnreadCountResponse(
    @SerializedName("unread_count") val unreadCount: Int
)

data class MarkReadResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("message") val message: String
)

// ── Health ────────────────────────────────────────────────────────────────────

// FIX: Added all fields returned by the actual HealthCheckResponse schema.
// The backend returns status="healthy" (not "ok") plus additional fields.
// Missing fields with default=null are safe — Gson ignores unknown JSON keys.
data class HealthResponse(
    @SerializedName("status")               val status: String,
    @SerializedName("application")          val application: String? = null,
    @SerializedName("version")              val version: String? = null,
    @SerializedName("stage")                val stage: String? = null,
    @SerializedName("database_connected")   val databaseConnected: Boolean? = null,
    @SerializedName("database_latency_ms")  val databaseLatencyMs: Double? = null,
    @SerializedName("database_message")     val databaseMessage: String? = null,
    @SerializedName("uptime_seconds")       val uptimeSeconds: Double? = null,
    @SerializedName("timestamp")            val timestamp: String? = null
)

data class ThreatIndicatorDto(
    @SerializedName("indicator_type")    val indicatorType: String = "DOMAIN",
    @SerializedName("indicator_value")   val indicatorValue: String,
    @SerializedName("threat_type")       val threatType: String? = null,
    @SerializedName("severity")          val severity: String? = null
)

data class DetailedHealthComponent(
    @SerializedName("status")  val status: String,
    @SerializedName("message") val message: String?
)

data class DetailedHealthResponse(
    @SerializedName("status")     val status: String,
    @SerializedName("components") val components: Map<String, DetailedHealthComponent>?
)

// ── Authentication & User Account ─────────────────────────────────────────────

data class UserRegisterRequestDto(
    @SerializedName("email")         val email: String,
    @SerializedName("username")      val username: String,
    @SerializedName("password")      val password: String,
    @SerializedName("full_name")     val fullName: String?,
    @SerializedName("mobile_number") val mobileNumber: String?,
    @SerializedName("consent_given") val consentGiven: Boolean = true
)

data class UserLoginRequestDto(
    @SerializedName("identifier") val identifier: String,
    @SerializedName("password")   val password: String
)

data class TokenResponseDto(
    @SerializedName("access_token")       val accessToken: String,
    @SerializedName("token_type")         val tokenType: String = "bearer",
    @SerializedName("user_id")            val userId: Int,
    @SerializedName("username")           val username: String,
    @SerializedName("email")              val email: String,
    @SerializedName("mobile_number")      val mobileNumber: String?,
    @SerializedName("is_mobile_verified") val isMobileVerified: Boolean,
    @SerializedName("is_email_verified")  val isEmailVerified: Boolean,
    @SerializedName("role")               val role: String
)

data class UserProfileResponseDto(
    @SerializedName("id")                 val id: Int,
    @SerializedName("username")           val username: String,
    @SerializedName("email")              val email: String,
    @SerializedName("full_name")          val fullName: String?,
    @SerializedName("mobile_number")      val mobileNumber: String?,
    @SerializedName("is_mobile_verified") val isMobileVerified: Boolean,
    @SerializedName("is_email_verified")  val isEmailVerified: Boolean,
    @SerializedName("consent_given")      val consentGiven: Boolean,
    @SerializedName("role")               val role: String,
    @SerializedName("created_at")         val createdAt: String
)

data class MobileOtpRequestDto(
    @SerializedName("mobile_number") val mobileNumber: String
)

data class MobileOtpVerifyRequestDto(
    @SerializedName("otp") val otp: String
)

// ── Cybercrime Complaints ─────────────────────────────────────────────────────

data class ComplaintDraftRequestDto(
    @SerializedName("complaint_category") val complaintCategory: String,
    @SerializedName("suspect_identifier") val suspectIdentifier: String?,
    @SerializedName("financial_loss_inr") val financialLossInr: Double = 0.0,
    @SerializedName("description")        val description: String,
    @SerializedName("evidence_summary")   val evidenceSummary: String? = null,
    @SerializedName("evidence_json")      val evidenceJson: String? = null,
    @SerializedName("device_id")          val deviceId: String? = null
)

data class RecordAckRequestDto(
    @SerializedName("official_ack_number") val officialAckNumber: String,
    @SerializedName("notes")               val notes: String? = null
)

data class ComplaintResponseDto(
    @SerializedName("complaint_id")             val complaintId: String,
    @SerializedName("user_id")                  val userId: Int?,
    @SerializedName("device_id")                val deviceId: String?,
    @SerializedName("complaint_category")       val complaintCategory: String,
    @SerializedName("suspect_identifier")       val suspectIdentifier: String?,
    @SerializedName("financial_loss_inr")       val financialLossInr: Double,
    @SerializedName("description")              val description: String,
    @SerializedName("evidence_summary")         val evidenceSummary: String?,
    @SerializedName("official_portal_url")      val officialPortalUrl: String,
    @SerializedName("helpline_number")          val helplineNumber: String,
    @SerializedName("status")                   val status: String,
    @SerializedName("official_ack_number")      val officialAckNumber: String?,
    @SerializedName("official_submission_date") val officialSubmissionDate: String?,
    @SerializedName("official_notes")           val officialNotes: String?,
    @SerializedName("created_at")               val createdAt: String,
    @SerializedName("tracking_instructions")    val trackingInstructions: String
)

// ── Community Threat Intelligence ─────────────────────────────────────────────

data class CommunityReportRequestDto(
    @SerializedName("indicator")      val indicator: String,
    @SerializedName("indicator_type") val indicatorType: String,
    @SerializedName("category")       val category: String,
    @SerializedName("description")    val description: String?,
    @SerializedName("severity")       val severity: String = "HIGH",
    @SerializedName("device_id")      val deviceId: String? = null
)

data class CommunityReportResponseDto(
    @SerializedName("indicator")        val indicator: String,
    @SerializedName("indicator_type")   val indicatorType: String,
    @SerializedName("category")         val category: String,
    @SerializedName("total_reports")    val totalReports: Int,
    @SerializedName("severity")         val severity: String,
    @SerializedName("verified_status")  val verifiedStatus: String,
    @SerializedName("status")           val status: String,
    @SerializedName("message")          val message: String
)

// ── Keypad User Protection (Elderly Shield) ──────────────────────────────────

data class KeypadElderlyUserCreateRequest(
    @SerializedName("full_name")          val fullName: String,
    @SerializedName("mobile_number")      val mobileNumber: String,
    @SerializedName("relationship")       val relationship: String = "Parent",
    @SerializedName("device_type")        val deviceType: String = "Nokia 105",
    @SerializedName("preferred_language") val preferredLanguage: String = "en",
    @SerializedName("consent_given")      val consentGiven: Boolean = true,
    @SerializedName("consent_notes")      val consentNotes: String? = null
)

typealias KeypadElderlyUserCreateDto = KeypadElderlyUserCreateRequest
typealias KeypadIncidentDto = KeypadIncidentItemDto

data class KeypadElderlyUserResponseDto(
    @SerializedName("id")                   val id: Int,
    @SerializedName("guardian_user_id")     val guardianUserId: Int,
    @SerializedName("full_name")            val fullName: String,
    @SerializedName("mobile_number")        val mobileNumber: String,
    @SerializedName("masked_mobile_number") val maskedMobileNumber: String,
    @SerializedName("relationship")         val relationship: String,
    @SerializedName("device_type")          val deviceType: String,
    @SerializedName("preferred_language")   val preferredLanguage: String,
    @SerializedName("consent_given")        val consentGiven: Boolean,
    @SerializedName("is_active")            val isActive: Boolean,
    @SerializedName("created_at")           val createdAt: String
)

data class KeypadSmsCheckRequestDto(
    @SerializedName("elderly_user_id")    val elderlyUserId: Int? = null,
    @SerializedName("sender")             val sender: String? = null,
    @SerializedName("message")            val message: String,
    @SerializedName("preferred_language") val preferredLanguage: String = "en"
)

data class KeypadSmsCheckResponseDto(
    @SerializedName("risk_score")             val riskScore: Double,
    @SerializedName("risk_level")             val riskLevel: String,
    @SerializedName("category")               val category: String,
    @SerializedName("matched_signatures")     val matchedSignatures: List<String>,
    @SerializedName("explanation")            val explanation: String,
    @SerializedName("recommended_action")     val recommendedAction: String,
    @SerializedName("golden_rule")            val goldenRule: String,
    @SerializedName("helpline")               val helpline: String,
    @SerializedName("is_automatic_detection") val isAutomaticDetection: Boolean = false,
    @SerializedName("disclaimer")             val disclaimer: String
)

data class KeypadCallCheckRequestDto(
    @SerializedName("elderly_user_id")         val elderlyUserId: Int? = null,
    @SerializedName("phone_number")            val phoneNumber: String,
    @SerializedName("claimed_caller_identity") val claimedCallerIdentity: String? = null,
    @SerializedName("preferred_language")      val preferredLanguage: String = "en"
)

data class KeypadCallCheckResponseDto(
    @SerializedName("phone_number")          val phoneNumber: String,
    @SerializedName("normalized_number")     val normalizedNumber: String,
    @SerializedName("risk_level")            val riskLevel: String,
    @SerializedName("risk_score")            val riskScore: Double,
    @SerializedName("fraud_category")        val fraudCategory: String?,
    @SerializedName("report_count")          val reportCount: Int,
    @SerializedName("is_verified_authority") val isVerifiedAuthority: Boolean,
    @SerializedName("verification_status")   val verificationStatus: String,
    @SerializedName("explanation")           val explanation: String,
    @SerializedName("recommended_action")    val recommendedAction: String,
    @SerializedName("reporting_helpline")    val reportingHelpline: String,
    @SerializedName("is_automatic_blocking") val isAutomaticBlocking: Boolean = false,
    @SerializedName("disclaimer")            val disclaimer: String
)

data class KeypadScamNumberReportRequestDto(
    @SerializedName("elderly_user_id")         val elderlyUserId: Int? = null,
    @SerializedName("phone_number")            val phoneNumber: String,
    @SerializedName("fraud_category")          val fraudCategory: String = "SUSPICIOUS_CALL",
    @SerializedName("claimed_caller_identity") val claimedCallerIdentity: String? = null,
    @SerializedName("evidence_notes")          val evidenceNotes: String? = null
)

data class KeypadScamNumberReportResponseDto(
    @SerializedName("id")                  val id: Int,
    @SerializedName("normalized_number")   val normalizedNumber: String,
    @SerializedName("status")              val status: String,
    @SerializedName("message")             val message: String,
    @SerializedName("verification_status") val verificationStatus: String
)

data class KeypadIncidentItemDto(
    @SerializedName("id")                 val id: Int,
    @SerializedName("guardian_user_id")   val guardianUserId: Int,
    @SerializedName("elderly_user_id")    val elderlyUserId: Int?,
    @SerializedName("elderly_user_name")  val elderlyUserName: String?,
    @SerializedName("incident_type")      val incidentType: String,
    @SerializedName("indicator")          val indicator: String,
    @SerializedName("risk_score")         val riskScore: Double,
    @SerializedName("severity")           val severity: String,
    @SerializedName("category")           val category: String,
    @SerializedName("explanation")        val explanation: String,
    @SerializedName("recommended_action") val recommendedAction: String,
    @SerializedName("is_acknowledged")    val isAcknowledged: Boolean,
    @SerializedName("created_at")         val createdAt: String
)

data class KeypadAlertSummaryResponseDto(
    @SerializedName("total_dependents")      val totalDependents: Int,
    @SerializedName("total_incidents")       val totalIncidents: Int,
    @SerializedName("unacknowledged_alerts") val unacknowledgedAlerts: Int,
    @SerializedName("critical_alerts")       val criticalAlerts: Int,
    @SerializedName("high_alerts")           val highAlerts: Int,
    @SerializedName("recent_incidents")      val recentIncidents: List<KeypadIncidentItemDto>
)

data class KeypadEducationTopicDto(
    @SerializedName("topic_id")          val topicId: String,
    @SerializedName("title")             val title: String,
    @SerializedName("summary")           val summary: String,
    @SerializedName("danger_indicators") val dangerIndicators: List<String>,
    @SerializedName("safe_behavior")     val safeBehavior: String
)

data class KeypadEducationResponseDto(
    @SerializedName("language")                val language: String,
    @SerializedName("language_label")          val languageLabel: String,
    @SerializedName("golden_rule_title")       val goldenRuleTitle: String,
    @SerializedName("golden_rule_description") val goldenRuleDescription: String,
    @SerializedName("do_not_share_items")      val doNotShareItems: List<String>,
    @SerializedName("common_scams")            val commonScams: List<KeypadEducationTopicDto>,
    @SerializedName("helpline_guidance")       val helplineGuidance: String
)

data class KeypadHelpdeskEntryDto(
    @SerializedName("name")           val name: String,
    @SerializedName("purpose")        val purpose: String,
    @SerializedName("access_channel") val accessChannel: String,
    @SerializedName("contact_or_url") val contactOrUrl: String,
    @SerializedName("how_it_helps")   val howItHelps: String
)

data class KeypadOfficialHelpdeskResponseDto(
    @SerializedName("disclaimer")          val disclaimer: String,
    @SerializedName("portals")             val portals: List<Map<String, Any>>,
    @SerializedName("helplines")           val helplines: List<KeypadHelpdeskEntryDto>,
    @SerializedName("legal_clarification") val legalClarification: String
)

