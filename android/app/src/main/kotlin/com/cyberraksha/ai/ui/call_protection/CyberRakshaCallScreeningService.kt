package com.cyberraksha.ai.ui.call_protection

import android.os.Build
import android.telecom.Call
import android.telecom.CallScreeningService
import android.telephony.PhoneNumberUtils
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.room.Room
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.local.AppDatabase
import com.cyberraksha.ai.data.local.ThreatIncidentEntity
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.remote.NumberCheckRequest
import com.cyberraksha.ai.data.remote.SecurityEventApiRequest
import com.cyberraksha.ai.notifications.NotificationHelper
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.firstOrNull
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull

@RequiresApi(Build.VERSION_CODES.Q)
class CyberRakshaCallScreeningService : CallScreeningService() {

    companion object {
        private const val TAG = "CyberRakshaCallShield"
    }

    private val serviceScope = CoroutineScope(Dispatchers.IO)

    override fun onScreenCall(callDetails: Call.Details) {
        val rawHandle = callDetails.handle?.schemeSpecificPart ?: ""
        if (rawHandle.isBlank()) {
            allowCall(callDetails)
            return
        }

        // Safety 1: Never block emergency numbers under any circumstances
        try {
            if (PhoneNumberUtils.isEmergencyNumber(rawHandle)) {
                Log.i(TAG, "Emergency call identified ($rawHandle). Permitted immediately.")
                allowCall(callDetails)
                return
            }
        } catch (e: Exception) {
            Log.w(TAG, "Error checking emergency number: ${e.message}")
        }

        // Safety 2: Never block recognized contacts automatically
        val callerName = callDetails.callerDisplayName?.toString()?.trim() ?: ""
        val contactName = callDetails.contactDisplayName?.toString()?.trim() ?: ""
        if (callerName.isNotBlank() || contactName.isNotBlank()) {
            Log.d(TAG, "Recognized contact call ($rawHandle, '$contactName'). Permitted.")
            allowCall(callDetails)
            return
        }

        serviceScope.launch {
            val prefs = AppPreferences(applicationContext)
            val autoEnabled = prefs.autonomousProtectionEnabled.firstOrNull() ?: true
            val callEnabled = prefs.callProtectionEnabled.firstOrNull() ?: true
            val blockingEnabled = prefs.callBlockingEnabled.firstOrNull() ?: true

            if (!autoEnabled || !callEnabled) {
                Log.d(TAG, "Call protection is disabled in settings. Allowing call.")
                allowCall(callDetails)
                return@launch
            }

            val registeredId = prefs.deviceId.firstOrNull() ?: "android-call-screener"
            val backendUrl = prefs.backendUrl.firstOrNull() ?: AppPreferences.DEFAULT_BACKEND_URL
            val api = NetworkModule.getApiService(backendUrl)

            // Telecom framework requires response within ~5 seconds; enforce strict sub-3s timeout for fail-open safety
            val result = withTimeoutOrNull(3000L) {
                try {
                    val res = api.checkNumber(
                        NumberCheckRequest(
                            deviceId = registeredId,
                            phoneNumber = rawHandle
                        )
                    )
                    if (res.isSuccessful) res.body() else null
                } catch (e: Exception) {
                    Log.w(TAG, "Call reputation check failed or offline: ${e.message}")
                    null
                }
            }

            val db = Room.databaseBuilder(
                applicationContext,
                AppDatabase::class.java,
                "cyber_raksha_db"
            ).fallbackToDestructiveMigration().build()

            val currentUserId = prefs.userEmail.firstOrNull() ?: prefs.userName.firstOrNull() ?: prefs.deviceId.firstOrNull()

            try {
                if (result != null && result.riskLevel.equals("CRITICAL", ignoreCase = true)) {
                    val category = result.fraudCategory ?: "EXTORTION_OR_DIGITAL_ARREST"

                    if (blockingEnabled) {
                        // High probability fraud / digital arrest attempt: reject call
                        val response = CallResponse.Builder()
                            .setDisallowCall(true)
                            .setRejectCall(true)
                            .setSkipCallLog(false)
                            .setSkipNotification(false)
                            .build()

                        respondToCall(callDetails, response)
                        Log.i(TAG, "BLOCKED CRITICAL fraud call from $rawHandle ($category)")
                    } else {
                        // User opted for warn-only
                        allowCall(callDetails)
                        Log.w(TAG, "CRITICAL fraud call detected but user configured warn-only: $rawHandle")
                    }

                    // 1. Record in local incident table with unified architecture
                    val incId = db.threatIncidentDao().insertIncident(
                        ThreatIncidentEntity(
                            incidentType = "CALL",
                            indicator = rawHandle,
                            category = category,
                            severity = "CRITICAL",
                            riskScore = 95.0f,
                            description = if (blockingEnabled) "Blocked extortion/fraud call from $rawHandle ($category)" else "Warned of critical extortion call from $rawHandle ($category)",
                            timestamp = System.currentTimeMillis(),
                            isSynced = false,
                            userId = currentUserId,
                            originalContent = "Incoming call from $rawHandle",
                            detectionExplanation = "High-confidence digital arrest / telecom impersonation threat matching verified fraud telemetry.",
                            recommendedAction = if (blockingEnabled) "Call was screened and blocked automatically." else "Do not engage; do not transfer money or share identity documents."
                        )
                    )

                    // 2. High-priority notification
                    NotificationHelper.showNotification(
                        context = applicationContext,
                        title = if (blockingEnabled) "🚨 Scam Call Blocked" else "🚨 CRITICAL Threat Call Warning",
                        message = "Caller: ${result.normalizedNumber}\nCategory: $category\nAction: ${if (blockingEnabled) "Automatically blocked" else "Warning issued - do not answer"}",
                        severity = "CRITICAL",
                        notificationId = rawHandle.hashCode()
                    )

                    // 3. Telemetry
                    try {
                        api.reportSecurityEvent(
                            SecurityEventApiRequest(
                                eventType = if (blockingEnabled) "CALL_FRAUD_INTERCEPTED" else "CALL_FRAUD_WARNED",
                                severity = "CRITICAL",
                                sourceComponent = "ANDROID_CALL_SCREENING",
                                deviceId = registeredId,
                                threatIndicator = rawHandle,
                                riskScore = 95.0f,
                                detectionReason = category,
                                description = "Incoming scam call from $rawHandle ($category)"
                            )
                        )
                        db.threatIncidentDao().markAsSynced(listOf(incId))
                    } catch (_: Exception) {}

                } else if (result != null && result.riskLevel.equals("HIGH", ignoreCase = true)) {
                    // High risk: fail-open allow ring but display warning notification
                    allowCall(callDetails)
                    Log.w(TAG, "WARNING: Suspicious call permitted to ring from $rawHandle")

                    val category = result.fraudCategory ?: "SUSPICIOUS_CALL"

                    val incId = db.threatIncidentDao().insertIncident(
                        ThreatIncidentEntity(
                            incidentType = "CALL",
                            indicator = rawHandle,
                            category = category,
                            severity = "HIGH",
                            riskScore = 75.0f,
                            description = "Suspicious call from $rawHandle reported for $category",
                            timestamp = System.currentTimeMillis(),
                            isSynced = false,
                            userId = currentUserId,
                            originalContent = "Incoming call from $rawHandle",
                            detectionExplanation = "Number has multiple fraud complaints or untrusted telecom profile.",
                            recommendedAction = "Verify caller identity independently; never share OTP or banking details."
                        )
                    )

                    NotificationHelper.showNotification(
                        context = applicationContext,
                        title = "⚠️ Suspicious Caller Warning",
                        message = "Caller: ${result.normalizedNumber}\nReason: $category\nAdvice: Exercise caution; do not share OTP.",
                        severity = "HIGH",
                        notificationId = rawHandle.hashCode()
                    )

                    try {
                        api.reportSecurityEvent(
                            SecurityEventApiRequest(
                                eventType = "SUSPICIOUS_CALL_WARNED",
                                severity = "HIGH",
                                sourceComponent = "ANDROID_CALL_SCREENING",
                                deviceId = registeredId,
                                threatIndicator = rawHandle,
                                riskScore = 75.0f,
                                detectionReason = category,
                                description = "Warned user of incoming suspicious call from $rawHandle"
                            )
                        )
                        db.threatIncidentDao().markAsSynced(listOf(incId))
                    } catch (_: Exception) {}

                } else {
                    // Safe / Unflagged / Fail-Open
                    allowCall(callDetails)
                }
            } finally {
                db.close()
            }
        }
    }

    private fun allowCall(callDetails: Call.Details) {
        val response = CallResponse.Builder()
            .setDisallowCall(false)
            .build()
        respondToCall(callDetails, response)
    }
}
