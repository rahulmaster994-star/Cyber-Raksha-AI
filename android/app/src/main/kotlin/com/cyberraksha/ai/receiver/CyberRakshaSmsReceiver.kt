package com.cyberraksha.ai.receiver

import android.Manifest
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Telephony
import android.util.Log
import androidx.core.content.ContextCompat
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
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.firstOrNull
import java.util.concurrent.ConcurrentHashMap

class CyberRakshaSmsReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "CyberRakshaSmsReceiver"
        // 5-second deduplication cache for multipart PDU reassembly
        private val recentAlertCache = ConcurrentHashMap<String, Long>()
    }

    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action
        if (action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION && action != "android.provider.Telephony.SMS_RECEIVED") {
            return
        }

        val messages = try {
            Telephony.Sms.Intents.getMessagesFromIntent(intent)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse SMS messages from broadcast intent", e)
            null
        }

        if (messages.isNullOrEmpty()) {
            Log.w(TAG, "SMS broadcast received but message list is empty or unparseable.")
            return
        }

        val sender = messages[0].displayOriginatingAddress
            ?: messages[0].originatingAddress
            ?: "Unknown"

        val fullBody = messages.joinToString("") {
            it.displayMessageBody ?: it.messageBody ?: ""
        }

        if (fullBody.isBlank()) {
            Log.w(TAG, "SMS broadcast received but message body is blank.")
            return
        }

        val maskedSender = SmsReceiverDiagnostics.maskSender(sender)
        Log.i(TAG, "SMS Broadcast intercepted: sender=$maskedSender, parts=${messages.size}, chars=${fullBody.length}")

        // Asynchronous processing using goAsync()
        val pendingResult = goAsync()
        CoroutineScope(Dispatchers.IO).launch {
            try {
                processIncomingSms(context, sender, fullBody, messages.size)
            } catch (e: Exception) {
                Log.e(TAG, "Unhandled exception processing incoming SMS", e)
            } finally {
                pendingResult.finish()
            }
        }
    }

    private suspend fun processIncomingSms(context: Context, sender: String, body: String, partsCount: Int) {
        val prefs = AppPreferences(context)

        val hasReceiveSms = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.RECEIVE_SMS
        ) == PackageManager.PERMISSION_GRANTED

        val hasPostNotif = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
        } else true

        val autonomousEnabled = prefs.autonomousProtectionEnabled.firstOrNull() ?: true
        val smsProtectionEnabled = prefs.smsProtectionEnabled.firstOrNull() ?: true

        if (!autonomousEnabled || !smsProtectionEnabled) {
            Log.d(TAG, "SMS protection is toggled off in settings (autonomous=$autonomousEnabled, sms=$smsProtectionEnabled).")
            SmsReceiverDiagnostics.recordTrace(
                SmsReceiverDiagnostics.SmsTrace(
                    senderMasked = SmsReceiverDiagnostics.maskSender(sender),
                    partsCount = partsCount,
                    charLength = body.length,
                    category = "DISABLED",
                    riskScore = 0f,
                    severity = "LOW",
                    reasonsCount = 0,
                    notificationPosted = false,
                    incidentSaved = false,
                    permissionReceiveSms = hasReceiveSms,
                    permissionPostNotifications = hasPostNotif,
                    statusMessage = "Protection disabled by user toggle in settings"
                )
            )
            return
        }

        // 1. Run Unified AI Risk Analysis
        val assessment = UnifiedRiskEngine.evaluate(body, sender)
        val maskedSender = SmsReceiverDiagnostics.maskSender(sender)
        Log.i(TAG, "SMS Evaluated: category=${assessment.category}, risk=${assessment.riskScore}, severity=${assessment.severity}")

        // 2. Multi-part Deduplication (5-second window)
        val deduplicationKey = "${sender}_${assessment.category}_${body.hashCode()}"
        val now = System.currentTimeMillis()
        val lastSeen = recentAlertCache[deduplicationKey]
        if (lastSeen != null && (now - lastSeen) < 5_000L) {
            Log.d(TAG, "Duplicate SMS threat suppressed within 5s deduplication window: $deduplicationKey")
            return
        }
        recentAlertCache[deduplicationKey] = now

        // 3. Database Persistence
        val db = Room.databaseBuilder(
            context.applicationContext,
            AppDatabase::class.java,
            "cyber_raksha_db"
        ).fallbackToDestructiveMigration().build()

        var incidentSaved = false
        var notificationPosted = false
        var incidentId: Long = -1

        try {
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

            // 4. If Threat is Detected (HIGH or CRITICAL): Persist and Alert IMMEDIATELY
            if (assessment.severity == "HIGH" || assessment.severity == "CRITICAL") {
                val currentUserId = prefs.userEmail.firstOrNull() ?: prefs.userName.firstOrNull() ?: prefs.deviceId.firstOrNull()

                incidentId = db.threatIncidentDao().insertIncident(
                    ThreatIncidentEntity(
                        incidentType = "SMS",
                        indicator = sender,
                        category = assessment.category,
                        severity = assessment.severity,
                        riskScore = assessment.riskScore,
                        description = "Automated SMS threat intercepted from $sender: ${assessment.reasons.firstOrNull() ?: assessment.category}",
                        timestamp = System.currentTimeMillis(),
                        isSynced = false,
                        userId = currentUserId,
                        originalContent = body,
                        detectionExplanation = assessment.reasons.joinToString("; "),
                        recommendedAction = assessment.recommendedAction
                    )
                )
                incidentSaved = true

                // Build Alert Title
                val notificationTitle = when (assessment.category) {
                    "GOV_IMPERSONATION" -> "🚨 Digital Arrest / Police Scam Blocked"
                    "OTP_THEFT"          -> "⚠️ Critical OTP Theft Attempt Detected"
                    "UPI_FRAUD"          -> "🚨 UPI Payment Fraud SMS Intercepted"
                    "BANKING_FRAUD"      -> "⚠️ Fake Bank KYC / Suspension Alert"
                    "DELIVERY_SCAM"      -> "📦 Delivery Phishing SMS Detected"
                    "LOAN_SCAM"          -> "⚠️ Unauthorized Loan Scam Detected"
                    else                 -> "⚠️ High-Risk Fraud SMS Detected"
                }

                val notificationMessage = "Sender: $sender\n${assessment.recommendedAction}"

                notificationPosted = NotificationHelper.showNotification(
                    context = context,
                    title = notificationTitle,
                    message = notificationMessage,
                    severity = assessment.severity,
                    notificationId = deduplicationKey.hashCode()
                )
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error persisting SMS incident to Room database", e)
        } finally {
            db.close()
        }

        // Record diagnostic trace
        SmsReceiverDiagnostics.recordTrace(
            SmsReceiverDiagnostics.SmsTrace(
                senderMasked = maskedSender,
                partsCount = partsCount,
                charLength = body.length,
                category = assessment.category,
                riskScore = assessment.riskScore,
                severity = assessment.severity,
                reasonsCount = assessment.reasons.size,
                notificationPosted = notificationPosted,
                incidentSaved = incidentSaved,
                permissionReceiveSms = hasReceiveSms,
                permissionPostNotifications = hasPostNotif,
                statusMessage = if (assessment.severity == "HIGH" || assessment.severity == "CRITICAL") {
                    "Threat intercepted and alert issued"
                } else {
                    "Message analyzed as benign"
                }
            )
        )

        // 5. Cloud Telemetry Sync (Bound by 3-second timeout so receiver finishes instantly)
        if (incidentSaved && incidentId > 0) {
            try {
                withTimeoutOrNull(3000L) {
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
                            rawPayload = "{\"sender\":\"$sender\",\"urls\":${Gson().toJson(assessment.extractedUrls)}}"
                        )
                    )

                    if (response.isSuccessful) {
                        val syncDb = Room.databaseBuilder(
                            context.applicationContext,
                            AppDatabase::class.java,
                            "cyber_raksha_db"
                        ).fallbackToDestructiveMigration().build()
                        syncDb.threatIncidentDao().markAsSynced(listOf(incidentId))
                        syncDb.close()
                        Log.i(TAG, "SMS threat telemetry synced to backend successfully.")
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Offline/timeout syncing SMS telemetry; queued for WorkManager: ${e.message}")
            }
        }
    }
}
