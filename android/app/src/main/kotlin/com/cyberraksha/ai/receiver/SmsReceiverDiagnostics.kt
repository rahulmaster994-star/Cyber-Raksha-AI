package com.cyberraksha.ai.receiver

object SmsReceiverDiagnostics {

    data class SmsTrace(
        val timestamp: Long = System.currentTimeMillis(),
        val senderMasked: String,
        val partsCount: Int,
        val charLength: Int,
        val category: String,
        val riskScore: Float,
        val severity: String,
        val reasonsCount: Int,
        val notificationPosted: Boolean,
        val incidentSaved: Boolean,
        val permissionReceiveSms: Boolean,
        val permissionPostNotifications: Boolean,
        val statusMessage: String
    )

    @Volatile
    var lastTrace: SmsTrace? = null
        private set

    @Volatile
    var totalBroadcastsReceived: Int = 0
        private set

    @Volatile
    var totalThreatsDetected: Int = 0
        private set

    fun recordTrace(trace: SmsTrace) {
        lastTrace = trace
        totalBroadcastsReceived++
        if (trace.severity == "HIGH" || trace.severity == "CRITICAL") {
            totalThreatsDetected++
        }
    }

    fun maskSender(sender: String): String {
        return if (sender.length > 4) {
            sender.take(2) + "*".repeat(sender.length - 4) + sender.takeLast(2)
        } else {
            "****"
        }
    }
}

