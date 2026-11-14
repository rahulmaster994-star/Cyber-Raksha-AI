package com.cyberraksha.ai.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.util.Log
import androidx.room.Room
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.local.AppDatabase
import com.cyberraksha.ai.data.local.SmsAnalysisEntity
import com.cyberraksha.ai.data.local.ThreatIncidentEntity
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.remote.SecurityEventApiRequest
import com.cyberraksha.ai.engine.UnifiedRiskEngine
import com.cyberraksha.ai.notifications.NotificationHelper
import com.google.gson.Gson
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.firstOrNull
import kotlinx.coroutines.launch
import java.util.concurrent.ConcurrentHashMap

class CyberRakshaSmsReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "CyberRakshaSmsReceiver"
        // In-memory deduplication cache: hash -> timestamp (expires after 60s)
        private val recentAlertCache = ConcurrentHashMap<String, Long>()
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
        if (messages.isNullOrEmpty()) return

        val sender = messages[0].displayOriginatingAddress ?: "Unknown"
        val fullBody = messages.joinToString("") { it.displayMessageBody ?: "" }

        if (fullBody.isBlank()) return

        Log.i(TAG, "Incoming SMS intercepted from: $sender (length: ${fullBody.length})")

        // Asynchronous processing using goAsync() to prevent blocking the main thread
        val pendingResult = goAsync()
        CoroutineScope(Dispatchers.IO).launch {
            try {
                processIncomingSms(context, sender, fullBody)
            } catch (e: Exception) {
                Log.e(TAG, "Error processing incoming SMS", e)
            } finally {
                pendingResult.finish()
            }
        }
    }

    private suspend fun processIncomingSms(context: Context, sender: String, body: String) {
        val prefs = AppPreferences(context)

        // Check if master autonomous protection is active
        val autonomousEnabled = prefs.autonomousProtectionEnabled.firstOrNull() ?: true
        val smsProtectionEnabled = prefs.smsProtectionEnabled.firstOrNull() ?: true
        if (!autonomousEnabled || !smsProtectionEnabled) {
            Log.d(TAG, "SMS protection is disabled by user settings. Skipping automated analysis.")
            return
        }

        // 1. Run Autonomous AI Risk Analysis
        val assessment = UnifiedRiskEngine.evaluate(body, sender)
        Log.i(TAG, "SMS Evaluation Result -> Category: ${assessment.category}, Risk: ${assessment.riskScore}, Severity: ${assessment.severity}")

        // 2. Deduplication check
        val deduplicationKey = "${sender}_${assessment.category}_${body.hashCode()}"
        val now = System.currentTimeMillis()
        val lastSeen = recentAlertCache[deduplicationKey]
        if (lastSeen != null && (now - lastSeen) < 60_000L) {
            Log.d(TAG, "Duplicate SMS threat suppressed within 60s window: $deduplicationKey")
            return
        }
        recentAlertCache[deduplicationKey] = now

        // 3. Database persistence
        val db = Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "cyber_raksha_db"
        ).fallbackToDestructiveMigration().build()

        val gson = Gson()
        db.smsAnalysisDao().insertAnalysis(
            SmsAnalysisEntity(
                messageHash = body.hashCode().toString(),
                riskScore = assessment.riskScore,
                riskLevel = assessment.severity,
                fraudCategory = assessment.category,
                detectionReasonsJson = gson.toJson(assessment.reasons),
                recommendedAction = assessment.recommendedAction
            )
        )

        // 4. If Threat is Detected (HIGH or CRITICAL): Alert & Prevent
        if (assessment.severity == "HIGH" || assessment.severity == "CRITICAL") {
            // Record in unified incident table
            val incidentId = db.threatIncidentDao().insertIncident(
                ThreatIncidentEntity(
                    incidentType = "SMS",
                    indicator = sender,
                    category = assessment.category,
                    severity = assessment.severity,
                    riskScore = assessment.riskScore,
                    description = "Automated SMS threat intercepted from $sender: ${assessment.reasons.firstOrNull() ?: assessment.category}"
                )
            )

            // Trigger Immediate Prominent Security Notification
            val notificationTitle = when (assessment.category) {
                "GOV_IMPERSONATION" -> "🚨 Digital Arrest / Police Scam Blocked"
                "OTP_THEFT" -> "⚠️ Critical OTP Theft Attempt Detected"
                "UPI_FRAUD" -> "🚨 UPI Payment Fraud SMS Intercepted"
                "BANKING_FRAUD" -> "⚠️ Fake Bank KYC / Suspension Alert"
                "DELIVERY_SCAM" -> "📦 Delivery Phishing SMS Detected"
                else -> "⚠️ High-Risk SMS Threat Detected"
            }

            val notificationMessage = "Sender: $sender\n${assessment.recommendedAction}"

            NotificationHelper.showNotification(
                context = context,
                title = notificationTitle,
                message = notificationMessage,
                severity = assessment.severity,
                notificationId = deduplicationKey.hashCode()
            )

            // 5. Cloud Telemetry & Sync (Non-blocking)
            try {
                val deviceId = prefs.deviceId.firstOrNull() ?: "android-device"
                val backendUrl = prefs.backendUrl.firstOrNull() ?: AppPreferences.DEFAULT_BACKEND_URL
                val api = NetworkModule.getApiService(backendUrl)

                val response = api.reportSecurityEvent(
                    SecurityEventApiRequest(
                        eventType = "AUTOMATIC_SMS_THREAT_INTERCEPTED",
                        severity = assessment.severity,
                        sourceComponent = "ANDROID_SMS_RECEIVER",
                        deviceId = deviceId,
                        threatIndicator = assessment.extractedUrls.firstOrNull() ?: sender,
                        riskScore = assessment.riskScore,
                        detectionReason = assessment.reasons.firstOrNull() ?: assessment.category,
                        description = "Autonomous SMS fraud detection: ${assessment.category} from $sender",
                        rawPayload = "{\"sender\":\"$sender\",\"urls\":${gson.toJson(assessment.extractedUrls)}}"
                    )
                )

                if (response.isSuccessful) {
                    db.threatIncidentDao().markAsSynced(listOf(incidentId))
                    Log.i(TAG, "SMS threat incident successfully synchronized to backend.")
                }
            } catch (e: Exception) {
                Log.w(TAG, "Offline: Could not sync SMS security event immediately; queued for WorkManager.", e)
            }
        }
        db.close()
    }
}

