package com.cyberraksha.ai.service

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import androidx.room.Room
import com.cyberraksha.ai.data.local.AppDatabase
import com.cyberraksha.ai.data.local.ThreatIncidentEntity
import com.cyberraksha.ai.engine.UnifiedRiskEngine
import com.cyberraksha.ai.notifications.NotificationHelper
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

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
            ?: return

        // Ignore empty, call notifications, or short status messages
        if (text.length < 5 || text.contains("incoming call", ignoreCase = true) || text.contains("missed call", ignoreCase = true)) {
            return
        }

        val source = if (pkg.contains("whatsapp")) "WHATSAPP" else "TELEGRAM"

        serviceScope.launch {
            try {
                val eval = UnifiedRiskEngine.evaluate(text, title)
                if (eval.severity == "HIGH" || eval.severity == "CRITICAL") {
                    Log.w(TAG, "[$source THREAT DETECTED] Category: ${eval.category}, Score: ${eval.riskScore}")

                    // 1. Alert citizen immediately via high-priority notification
                    val notifTitle = "⚠️ [FRAUD DETECTED] $source Alert"
                    val notifBody = "Suspicious message from '$title' flagged as ${eval.category} (${eval.severity} Risk). Do not share OTP or click links."
                    NotificationHelper.showNotification(
                        context = applicationContext,
                        title = notifTitle,
                        message = notifBody,
                        severity = eval.severity,
                        notificationId = (System.currentTimeMillis() % 100000).toInt()
                    )

                    // 2. Persist threat incident into local Room database
                    val db = Room.databaseBuilder(
                        applicationContext,
                        AppDatabase::class.java,
                        "cyber_raksha_db"
                    ).fallbackToDestructiveMigration().build()

                    val incident = ThreatIncidentEntity(
                        incidentType = source,
                        indicator = title,
                        category = eval.category,
                        severity = eval.severity,
                        riskScore = eval.riskScore,
                        description = text,
                        timestamp = System.currentTimeMillis(),
                        isSynced = false
                    )
                    db.threatIncidentDao().insertIncident(incident)
                }
            } catch (e: Throwable) {
                Log.e(TAG, "Error evaluating incoming $source notification", e)
            }
        }
    }
}
