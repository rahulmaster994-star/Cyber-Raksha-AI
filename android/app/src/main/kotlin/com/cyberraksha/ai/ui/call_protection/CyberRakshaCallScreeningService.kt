package com.cyberraksha.ai.ui.call_protection

import android.os.Build
import android.telecom.Call
import android.telecom.CallScreeningService
import androidx.annotation.RequiresApi
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.data.remote.NumberCheckRequest
import com.cyberraksha.ai.notifications.NotificationHelper
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull

@RequiresApi(Build.VERSION_CODES.Q)
class CyberRakshaCallScreeningService : CallScreeningService() {

    private val serviceScope = CoroutineScope(Dispatchers.IO)

    override fun onScreenCall(callDetails: Call.Details) {
        val rawHandle = callDetails.handle?.schemeSpecificPart ?: ""
        if (rawHandle.isBlank()) {
            allowCall(callDetails)
            return
        }

        serviceScope.launch {
            // Telecom framework requires response within ~5 seconds
            val result = withTimeoutOrNull(3000L) {
                try {
                    val api = NetworkModule.getApiService()
                    val res = api.checkNumber(
                        NumberCheckRequest(
                            deviceId = "android-call-screener",
                            phoneNumber = rawHandle
                        )
                    )
                    if (res.isSuccessful) res.body() else null
                } catch (e: Exception) {
                    null
                }
            }

            if (result != null && result.riskLevel.equals("CRITICAL", ignoreCase = true)) {
                // High probability fraud / digital arrest attempt: reject call
                val response = CallResponse.Builder()
                    .setDisallowCall(true)
                    .setRejectCall(true)
                    .setSkipCallLog(false)
                    .setSkipNotification(false)
                    .build()

                respondToCall(callDetails, response)

                NotificationHelper.showNotification(
                    context = applicationContext,
                    title = "Scam Call Intercepted",
                    message = "Cyber Raksha blocked call from ${result.normalizedNumber}: ${result.fraudCategory ?: "Known Scam"}",
                    severity = "CRITICAL",
                    notificationId = System.currentTimeMillis().toInt()
                )
            } else if (result != null && result.riskLevel.equals("HIGH", ignoreCase = true)) {
                // High risk: allow ring but display warning notification
                allowCall(callDetails)

                NotificationHelper.showNotification(
                    context = applicationContext,
                    title = "Suspicious Caller Warning",
                    message = "Incoming call from ${result.normalizedNumber} reported for ${result.fraudCategory ?: "telecom fraud"}.",
                    severity = "HIGH",
                    notificationId = System.currentTimeMillis().toInt()
                )
            } else {
                allowCall(callDetails)
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
