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

