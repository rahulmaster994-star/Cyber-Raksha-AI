package com.cyberraksha.ai.ui.call_protection

import android.os.Build
import android.telecom.Call
import android.telecom.CallScreeningService
import androidx.annotation.RequiresApi
import android.util.Log
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

        serviceScope.launch {
            val prefs = AppPreferences(applicationContext)
            val autoEnabled = prefs.autonomousProtectionEnabled.firstOrNull() ?: true
            val callEnabled = prefs.callProtectionEnabled.firstOrNull() ?: true

            if (!autoEnabled || !callEnabled) {
                Log.d(TAG, "Call protection is disabled in settings. Allowing call.")
                allowCall(callDetails)
                return@launch
            }

            val registeredId = prefs.deviceId.firstOrNull() ?: "android-call-screener"
            val backendUrl = prefs.backendUrl.firstOrNull() ?: AppPreferences.DEFAULT_BACKEND_URL
            val api = NetworkModule.getApiService(backendUrl)

            // Telecom framework requires response within ~5 seconds
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

            try {
                if (result != null && result.riskLevel.equals("CRITICAL", ignoreCase = true)) {
                    // High probability fraud / digital arrest attempt: reject call
                    val response = CallResponse.Builder()
                        .setDisallowCall(true)
                        .setRejectCall(true)
                        .setSkipCallLog(false)
                        .setSkipNotification(false)
                        .build()

                    respondToCall(callDetails, response)
                    Log.i(TAG, "BLOCKED CRITICAL fraud call from $rawHandle (${result.fraudCategory})")

                    // 1. Record in local incident table
                    val incId = db.threatIncidentDao().insertIncident(
                        ThreatIncidentEntity(
                            incidentType = "CALL",
                            indicator = rawHandle,
                            category = result.fraudCategory ?: "PHONE_FRAUD",
                            severity = "CRITICAL",
                            riskScore = 95.0f,
                            description = "Scam call blocked from $rawHandle: ${result.fraudCategory ?: "Suspected Digital Arrest / Impersonation"}"
                        )
                    )

                    // 2. Notification
                    NotificationHelper.showNotification(
                        context = applicationContext,
                        title = "🚨 Scam Call Blocked",
                        message = "Cyber Raksha blocked call from ${result.normalizedNumber}: ${result.fraudCategory ?: "Known Fraud"}",
                        severity = "CRITICAL",
                        notificationId = rawHandle.hashCode()
                    )

                    // 3. Telemetry
                    try {
                        api.reportSecurityEvent(
                            SecurityEventApiRequest(
                                eventType = "CALL_FRAUD_INTERCEPTED",
                                severity = "CRITICAL",
                                sourceComponent = "ANDROID_CALL_SCREENING",
                                deviceId = registeredId,
                                threatIndicator = rawHandle,
                                riskScore = 95.0f,
                                detectionReason = result.fraudCategory ?: "CRITICAL_CALL_FRAUD",
                                description = "Blocked incoming scam call from $rawHandle"
                            )
                        )
                        db.threatIncidentDao().markAsSynced(listOf(incId))
                    } catch (_: Exception) {}

                } else if (result != null && result.riskLevel.equals("HIGH", ignoreCase = true)) {
                    // High risk: allow ring but display warning notification
                    allowCall(callDetails)
                    Log.w(TAG, "WARNING: Suspicious call permitted to ring from $rawHandle")

                    val incId = db.threatIncidentDao().insertIncident(
                        ThreatIncidentEntity(
                            incidentType = "CALL",
                            indicator = rawHandle,
                            category = result.fraudCategory ?: "SUSPICIOUS_CALL",
                            severity = "HIGH",
                            riskScore = 75.0f,
                            description = "Suspicious call from $rawHandle reported for ${result.fraudCategory ?: "telecom fraud"}"
                        )
                    )

                    NotificationHelper.showNotification(
                        context = applicationContext,
                        title = "⚠️ Suspicious Caller Warning",
                        message = "Incoming call from ${result.normalizedNumber} reported for ${result.fraudCategory ?: "telecom fraud"}.",
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
                                detectionReason = result.fraudCategory ?: "SUSPICIOUS_CALL",
                                description = "Warned user of incoming suspicious call from $rawHandle"
                            )
                        )
                        db.threatIncidentDao().markAsSynced(listOf(incId))
                    } catch (_: Exception) {}

                } else {
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
