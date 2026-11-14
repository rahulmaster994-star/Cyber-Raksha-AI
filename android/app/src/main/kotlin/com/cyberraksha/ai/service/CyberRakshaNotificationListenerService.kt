package com.cyberraksha.ai.service

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import androidx.room.Room
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.local.AppDatabase
import com.cyberraksha.ai.data.local.ThreatIncidentEntity
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.remote.SecurityEventApiRequest
import com.cyberraksha.ai.engine.UnifiedRiskEngine
import com.cyberraksha.ai.notifications.NotificationHelper
import com.google.gson.Gson
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.firstOrNull
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull
import java.util.concurrent.ConcurrentHashMap

/**
 * Cyber Raksha AI - Real-Time WhatsApp & Telegram Notification Protection Service
 *
 * Privacy-preserving on-device listener that inspects incoming message previews from WhatsApp
 * and Telegram without accessing app private storage or reading unnotified chats.
 * Evaluates risk locally via UnifiedRiskEngine and alerts citizen instantly upon fraud detection.
 */
class CyberRakshaNotificationListenerService : NotificationListenerService() {

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    companion object {
        private const val TAG = "CyberRakshaNotifListen"
        val MONITORED_PACKAGES = setOf(
            "com.whatsapp",
            "com.whatsapp.w4b",
            "org.telegram.messenger",
            "org.thunderdog.challegram"
        )
        @Volatile
        var isServiceConnected: Boolean = false
            private set
        @Volatile
        var lastInspectedPackage: String? = null
            private set
        @Volatile
        var lastThreatDetected: String? = null
            private set

        // 5-second deduplication cache across notification updates
        private val recentAlertCache = ConcurrentHashMap<String, Long>()
    }

    override fun onListenerConnected() {
        super.onListenerConnected()
        isServiceConnected = true
        Log.i(TAG, "Cyber Raksha NotificationListenerService connected to Android system.")
    }

    override fun onListenerDisconnected() {
        super.onListenerDisconnected()
        isServiceConnected = false
        Log.w(TAG, "Cyber Raksha NotificationListenerService disconnected from Android system.")
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        super.onNotificationPosted(sbn)
        if (sbn == null) return

        val pkg = sbn.packageName ?: return
        if (pkg !in MONITORED_PACKAGES) return

        // Ignore our own notifications or ongoing system alerts
        if (pkg == applicationContext.packageName || sbn.isOngoing) return

        val extras = sbn.notification.extras ?: return
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString()?.trim() ?: "Unknown"
        val text = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString()?.trim()
            ?: extras.getCharSequence(Notification.EXTRA_TEXT)?.toString()?.trim()

        lastInspectedPackage = pkg

        if (text.isNullOrBlank()) {
            Log.d(TAG, "[$pkg] Empty notification text (preview hidden or media file). Skipping.")
            return
        }

        // Detect if notification previews are hidden by user privacy settings (e.g. "1 new message")
        if (text.matches(Regex("""^\d+\s+new\s+messages?$""", RegexOption.IGNORE_CASE)) ||
            text.equals("New message", ignoreCase = true) ||
            text.equals("WhatsApp", ignoreCase = true)) {
            Log.i(TAG, "[$pkg] Notification content is masked by user/lockscreen privacy settings: '$text'. Content cannot be analyzed without message preview.")
            return
        }

        // Ignore calls or standard non-content alerts
        if (text.length < 5 || text.contains("incoming call", ignoreCase = true) || text.contains("missed call", ignoreCase = true)) {
            return
        }

        val isWhatsApp = pkg.contains("whatsapp")
        val source = if (isWhatsApp) "WHATSAPP" else "TELEGRAM"

        // Deduplication: prevent duplicate alerts for the same message within 5 seconds
        val deduplicationKey = "${pkg}_${title}_${text.hashCode()}"
        val now = System.currentTimeMillis()
        val lastSeen = recentAlertCache[deduplicationKey]
        if (lastSeen != null && (now - lastSeen) < 5_000L) {
            Log.d(TAG, "Duplicate $source threat alert suppressed within 5s deduplication window")
            return
        }
        recentAlertCache[deduplicationKey] = now

        serviceScope.launch {
            try {
                val prefs = AppPreferences(applicationContext)
                val autoEnabled = prefs.autonomousProtectionEnabled.firstOrNull() ?: true
                val moduleEnabled = if (isWhatsApp) {
                    prefs.whatsappProtectionEnabled.firstOrNull() ?: true
                } else {
                    prefs.telegramProtectionEnabled.firstOrNull() ?: true
                }

                if (!autoEnabled || !moduleEnabled) {
                    Log.d(TAG, "$source protection is toggled off in settings.")
                    return@launch
                }

                val eval = UnifiedRiskEngine.evaluate(text, title)
                if (eval.severity == "HIGH" || eval.severity == "CRITICAL") {
                    lastThreatDetected = "$source: ${eval.category} (${eval.severity})"
                    Log.w(TAG, "[$source THREAT DETECTED] Category: ${eval.category}, Score: ${eval.riskScore}")

                    // 1. Alert citizen immediately via high-priority notification
                    val notifTitle = "⚠️ [FRAUD DETECTED] $source Alert"
                    val notifBody = "Suspicious message from '$title' flagged as ${eval.category} (${eval.severity} Risk).\n${eval.recommendedAction}"
                    NotificationHelper.showNotification(
                        context = applicationContext,
                        title = notifTitle,
                        message = notifBody,
                        severity = eval.severity,
                        notificationId = deduplicationKey.hashCode()
                    )

                    // 2. Persist threat incident into local Room database with unified incident structure
                    val db = Room.databaseBuilder(
                        applicationContext,
                        AppDatabase::class.java,
                        "cyber_raksha_db"
                    ).fallbackToDestructiveMigration().build()

                    val currentUserId = prefs.userEmail.firstOrNull() ?: prefs.userName.firstOrNull() ?: prefs.deviceId.firstOrNull()

                    val incident = ThreatIncidentEntity(
                        incidentType = source,
                        indicator = title,
                        category = eval.category,
                        severity = eval.severity,
                        riskScore = eval.riskScore,
                        description = "Automated $source threat intercepted from $title: ${eval.reasons.firstOrNull() ?: eval.category}",
                        timestamp = System.currentTimeMillis(),
                        isSynced = false,
                        userId = currentUserId,
                        originalContent = text,
                        detectionExplanation = eval.reasons.joinToString("; "),
                        recommendedAction = eval.recommendedAction
                    )
                    val incidentId = db.threatIncidentDao().insertIncident(incident)

                    // 3. Cloud Telemetry Sync (Bound by 3-second timeout)
                    try {
                        withTimeoutOrNull(3000L) {
                            val deviceId = prefs.deviceId.firstOrNull() ?: "android-device"
                            val backendUrl = prefs.backendUrl.firstOrNull() ?: AppPreferences.DEFAULT_BACKEND_URL
                            val api = NetworkModule.getApiService(backendUrl)

                            val response = api.reportSecurityEvent(
                                SecurityEventApiRequest(
                                    eventType = "AUTOMATIC_${source}_THREAT_INTERCEPTED",
                                    severity = eval.severity,
                                    sourceComponent = "ANDROID_$source",
                                    deviceId = deviceId,
                                    threatIndicator = eval.extractedUrls.firstOrNull() ?: title,
                                    riskScore = eval.riskScore,
                                    detectionReason = eval.reasons.firstOrNull() ?: eval.category,
                                    description = "Autonomous $source fraud detection: ${eval.category} from $title",
                                    rawPayload = "{\"sender\":\"$title\",\"urls\":${Gson().toJson(eval.extractedUrls)}}"
                                )
                            )
                            if (response.isSuccessful) {
                                db.threatIncidentDao().markAsSynced(listOf(incidentId))
                                Log.i(TAG, "$source threat telemetry synced to backend successfully.")
                            }
                        }
                    } catch (e: Exception) {
                        Log.w(TAG, "Offline/timeout syncing $source telemetry; queued for WorkManager: ${e.message}")
                    } finally {
                        db.close()
                    }
                }
            } catch (e: Throwable) {
                Log.e(TAG, "Error evaluating incoming $source notification", e)
            }
        }
    }
}
